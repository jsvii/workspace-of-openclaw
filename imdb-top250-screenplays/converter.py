"""Converter for IMSDb HTML screenplay to Fountain format."""

import re
import html


def convert_to_fountain(html_content: str) -> str:
    """Convert IMSDb HTML screenplay to Fountain format."""
    import html
    
    text = html_content
    
    # Find pre tag and extract content between them
    pre_start = text.find('<pre>')
    pre_end = text.rfind('</pre>')
    
    if pre_start != -1 and pre_end > pre_start:
        text = text[pre_start:pre_end]
    else:
        # Try alternative pre tag format
        pre_start = text.find('<pre ')
        if pre_start != -1:
            pre_end = text.rfind('</pre>')
            if pre_end > pre_start:
                text = text[pre_start:pre_end]
    
    # Remove pre tags
    text = re.sub(r'</?pre[^>]*>', '', text, flags=re.IGNORECASE)
    
    # Remove <b> tags and unescape HTML entities
    text = re.sub(r'</?b>', '', text)
    text = html.unescape(text)
    
    # Remove any remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Skip HTML header at the beginning - find first non-HTML line
    lines = text.split('\n')
    start_idx = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Skip HTML/script tags and empty lines, look for actual content
        if stripped and not stripped.startswith(('<', '//', 'if ')) and len(stripped) > 0:
            # This could be screenplay content
            if i < 30:  # In the first 30 lines, find the title
                start_idx = max(0, i - 1)  # Include one line before for context
                break
    
    if start_idx > 0:
        lines = lines[start_idx:]
    
    text = '\n'.join(lines)
    
    lines = text.splitlines()
    fountain_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        if not stripped:
            fountain_lines.append("")
            continue
        
        # Scene headings (INT., EXT., etc.)
        scene_match = re.match(r'^(\d+\s+)?(INT|EXT|I/E|INT/EXT)\.?\s+', stripped, re.IGNORECASE)
        if scene_match:
            scene = re.sub(r'^\d+\s+', '', stripped)
            fountain_lines.append(scene.upper())
            continue
        
        # Transitions (FADE IN, CUT TO, etc.)
        if stripped.isupper() and (stripped.endswith(':') or ' TO:' in stripped or stripped.startswith('FADE TO')):
            fountain_lines.append("> " + stripped)
            continue
        
        leading_whitespace = len(line) - len(line.lstrip())
        
        # Character names (indented 20+ spaces, all caps)
        if leading_whitespace >= 20 and stripped.isupper():
            fountain_lines.append(stripped)
            continue
        
        # Dialogue (indented 10-20 spaces, not all caps)
        if 10 <= leading_whitespace < 20 and not stripped.isupper():
            fountain_lines.append(stripped)
            continue
        
        # Parentheticals
        if 10 <= leading_whitespace < 25 and stripped.startswith('(') and stripped.endswith(')'):
            fountain_lines.append(stripped)
            continue
        
        # Possible characters with smaller indent (4-10 spaces, all caps, short)
        if 4 <= leading_whitespace < 10 and stripped.isupper() and len(stripped) < 30:
            fountain_lines.append(stripped)
            continue
        
        # Default: action/description
        fountain_lines.append(stripped)
    
    output = "\n".join(fountain_lines)
    # Remove excessive blank lines
    output = re.sub(r'\n{3,}', '\n\n', output)
    
    return output


def convert_html_to_fountain(html_content: str) -> str:
    """Convenience function to convert HTML to Fountain."""
    return convert_to_fountain(html_content)


if __name__ == "__main__":
    # Test with a file
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            html_content = f.read()
        fountain = convert_to_fountain(html_content)
        print(fountain)
