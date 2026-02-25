/* Tiny Scheme with call/cc - minimal */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <setjmp.h>

#define T_NUM 1
#define T_SYM 2
#define T_CONS 3
#define T_PRIM 4
#define T_LAMBDA 5

typedef struct obj { int type; union { double num; char *sym; struct obj *pair[2]; struct { struct obj *(*fn)(struct obj*); int n; } prim; struct { struct obj *args, *body, *env; } lambda; }; } *obj;

#define car(o) ((o)->pair[0])
#define cdr(o) ((o)->pair[1])
#define nil ((obj)0)
#define isNil(o) ((o)==0)
#define isNum(o) ((o)&&(o)->type==T_NUM)
#define isSym(o) ((o)&&(o)->type==T_SYM)
#define isCons(o) ((o)&&(o)->type==T_CONS)
#define isPrim(o) ((o)&&(o)->type==T_PRIM)
#define isLambda(o) ((o)&&(o)->type==T_LAMBDA)

obj env;
jmp_buf top_jb, cc_jb;
obj cc_val;

obj make_num(double n) { obj o=malloc(sizeof(*o)); o->type=T_NUM; o->num=n; return o; }
obj make_sym(char *s) { obj o=malloc(sizeof(*o)); o->type=T_SYM; o->sym=strdup(s); return o; }
obj make_prim(obj(*f)(obj),int n){obj o=malloc(sizeof(*o));o->type=T_PRIM;o->prim.fn=f;o->prim.n=n;return o;}
obj cons(obj a,obj b){obj o=malloc(sizeof(*o));o->type=T_CONS;o->pair[0]=a;o->pair[1]=b;return o;}

obj error(char *s){printf("Error: %s\n",s);longjmp(top_jb,1);return nil;}

obj assoc(obj k,obj e){for(;!isNil(e);e=cdr(e))if(car(car(e))==k)return car(e);return nil;}

obj eval(obj e,obj env);

obj bind(obj a,obj b,obj e){return isNil(a)?e:cons(cons(car(a),car(b)),bind(cdr(a),cdr(b),e));}

obj evlist(obj l,obj e){return isNil(l)?nil:cons(eval(car(l),e),evlist(cdr(l),e));}

obj apply(obj f,obj a){
  if(isPrim(f))return f->prim.fn(a);
  if(isLambda(f))return eval(car(f->lambda.body),bind(f->lambda.args,a,f->lambda.env));
  error("not fn");
  return nil;
}

obj p_add(obj a){double r=0;for(;!isNil(a);a=cdr(a))r+=car(a)->num;return make_num(r);}
obj p_sub(obj a){return isNil(cdr(a))?make_num(-car(a)->num):make_num(car(a)->num-car(cadr(a))->num);}
obj p_mul(obj a){double r=1;for(;!isNil(a);a=cdr(a))r*=car(a)->num;return make_num(r);}
obj p_div(obj a){return make_num(car(a)->num/cadr(a)->num);}
obj p_numeq(obj a){return car(a)->num==cadr(a)->num?make_sym("#t"):nil;}
obj p_less(obj a){return car(a)->num<cadr(a)->num?make_sym("#t"):nil;}
obj p_cons(obj a){return cons(car(a),cadr(a));}
obj p_car(obj a){return car(car(a));}
obj p_cdr(obj a){return cdr(car(a));}
obj p_null(obj a){return isNil(car(a))?make_sym("#t"):nil;}
obj p_eq(obj a){return car(a)==cadr(a)?make_sym("#t"):nil;}
obj p_sym(obj a){return isSym(car(a))?make_sym("#t"):nil;}
obj p_not(obj a){return isNil(car(a))?make_sym("#t"):nil;}

obj p_cc(obj a){cc_val=car(a);longjmp(cc_jb,1);return nil;}

obj p_read(obj a){
  int c=getchar();if(c==EOF)return nil;
  if(c=='('){obj r=nil,l=nil;
    while((c=getchar())!=EOF){
      if(c==' ')continue;
      if(c==')')break;
      ungetc(c,stdin);obj x=p_read(nil);
      if(isNil(r))r=l=cons(x,nil);else{cdr(l)=cons(x,nil);l=cdr(l);}
    }return r;
  }
  if(c=='\'')return cons(make_sym("quote"),cons(p_read(nil),nil));
  if(c>='0'&&c<='9'){double n=c-'0';while((c=getchar())>='0'&&c<='9')n=n*10+c-'0';ungetc(c,stdin);return make_num(n);}
  char s[32];int i=0;
  while((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='+'||c=='-'||c=='*'||c=='/'||c=='?')s[i++]=c, c=getchar();
  s[i]=0;ungetc(c,stdin);return make_sym(s);
}

obj p_print(obj a){
  obj x=car(a);
  if(isNil(x))printf("()");
  else if(isNum(x))printf("%.15g",x->num);
  else if(isSym(x))printf("%s",x->sym);
  else if(isCons(x)){
    printf("(");
    for(int f=1;!isNil(x);x=cdr(x)){
      if(!f)printf(" ");
      f=0;p_print(car(x));
    }printf(")");
  }
  return nil;
}

obj eval(obj e,obj env){
  if(isNum(e)||isNil(e))return e;
  if(isSym(e)){obj v=assoc(e,env);return isNil(v)?error("unbound"):cdr(v);}
  if(!isCons(e))return error("bad");
  obj op=car(e);
  if(isSym(op)){
    if(!strcmp(op->sym,"quote"))return car(cdr(e));
    if(!strcmp(op->sym,"if")){obj c=eval(car(cdr(e)),env);return isNil(c)?eval(car(cddr(cdr(e))),env):eval(car(cdr(cdr(e))),env);}
    if(!strcmp(op->sym,"lambda"))return (obj)((((unsigned long long)car(cdr(e)))<<16)|((unsigned long long)cdr(cdr(e))<<2)|5); /* hack: encode lambda */
    if(!strcmp(op->sym,"define")){env=cons(cons(car(cdr(e)),eval(car(cdr(cdr(e))),env)),env);return nil;}
    if(!strcmp(op->sym,"call/cc")){if(setjmp(cc_jb)==0)return apply(car(cdr(e)),cons(make_sym("#<cc>"),nil));else return cc_val;}
  }
  obj ev=evlist(e,env);
  return apply(car(ev),cdr(ev));
}

void init(){
  env=nil;
  env=cons(cons(make_sym("+"),make_prim(p_add,-1)),env);
  env=cons(cons(make_sym("-"),make_prim(p_sub,-1)),env);
  env=cons(cons(make_sym("*"),make_prim(p_mul,-1)),env);
  env=cons(cons(make_sym("/"),make_prim(p_div,2)),env);
  env=cons(cons(make_sym("="),make_prim(p_numeq,2)),env);
  env=cons(cons(make_sym("<"),make_prim(p_less,2)),env);
  env=cons(cons(make_sym("cons"),make_prim(p_cons,2)),env);
  env=cons(cons(make_sym("car"),make_prim(p_car,1)),env);
  env=cons(cons(make_sym("cdr"),make_prim(p_cdr,1)),env);
  env=cons(cons(make_sym("null?"),make_prim(p_null,1)),env);
  env=cons(cons(make_sym("eq?"),make_prim(p_eq,2)),env);
  env=cons(cons(make_sym("symbol?"),make_prim(p_sym,1)),env);
  env=cons(cons(make_sym("not"),make_prim(p_not,1)),env);
  env=cons(cons(make_sym("call/cc"),make_prim(p_cc,1)),env);
  env=cons(cons(make_sym("read"),make_prim(p_read,0)),env);
  env=cons(cons(make_sym("print"),make_prim(p_print,1)),env);
  env=cons(cons(make_sym("eval"),make_prim((obj(*)(obj))eval,1)),env);
}

int main(){
  init();
  setjmp(top_jb);
  while(printf("> "),fflush(stdout),!isNil(p_read(nil))){
    p_print(cons(eval(p_read(nil),env),nil));printf("\n");
  }
  return 0;
}
