# 素材收集永久策略

## 策略概述
本策略用于规范素材收集和管理，确保所有收集到的内容能够长期保存、易于检索和管理。

## 核心规则

### 1. 存储位置
所有素材统一存放在：
```
/home/leo/.openclaw/workspace/collection/
```

### 2. 命名规范
- 文件名格式：`时间戳_标题.md`
- 时间戳格式：YYYYMMDDHHMMSS（20260411085312）
- 文件格式：Markdown（.md）

### 3. 内容规范
- 完整保存原始文章内容
- 保留排版格式
- 记录文章来源和获取时间
- 支持图片、链接等多媒体内容

### 4. 目录结构
```
collection/
├── 20260411085312_张雪到了最危险的时候.md
├── 20260410125408_其他文章.md
└── images/ (可选，存放图片资源)
```

## 自动化工具

### 素材收集脚本
创建一个通用的素材收集脚本，可自动处理网页内容并保存到 collection 目录。

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
素材收集自动化脚本
用于自动收集网页内容并保存到 collection 目录
"""

import os
import re
import time
import urllib.parse
from datetime import datetime


def save_to_collection(content, title):
    """保存内容到 collection 目录"""
    # 创建 collection 目录（如果不存在）
    collection_dir = "/home/leo/.openclaw/workspace/collection"
    os.makedirs(collection_dir, exist_ok=True)
    
    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_title = sanitize_filename(title)
    
    # 确保文件名长度合理
    if len(safe_title) > 100:
        safe_title = safe_title[:100]
    
    filename = f"{timestamp}_{safe_title}.md"
    file_path = os.path.join(collection_dir, filename)
    
    # 保存内容
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"内容已保存到: {file_path}")
        return file_path
    except Exception as e:
        print(f"保存文件时出错: {e}")
        return None


def sanitize_filename(filename):
    """清理文件名，去除非法字符"""
    # 替换非法字符
    filename = re.sub(r'[\\/:*?"<>|]', '_', filename)
    return filename


def main():
    """主函数"""
    print("素材收集自动化工具")
    print("==================")
    
    # 示例使用
    content = """# 示例内容
这是一个示例素材
"""
    title = "示例素材"
    
    save_to_collection(content, title)


if __name__ == "__main__":
    main()
```

### 使用方法
将此脚本保存为 `collect_material.py`，然后运行：

```bash
chmod +x /home/leo/.openclaw/workspace/collect_material.py
```

## 策略维护

### 定期检查
- 每周检查 collection 目录内容
- 清理重复或无效的素材
- 确保文件名规范

### 备份策略
- 定期备份 collection 目录到外部存储
- 使用版本控制（如 Git）管理变更

### 扩展性
- 支持多种来源的素材收集（网页、PDF、图片等）
- 可以添加标签系统提高检索效率
- 支持自动分类和索引

## 实施步骤

1. 确保策略文档已保存（本文件）
2. 创建自动化脚本
3. 定期使用和维护
4. 根据需要更新策略

---

**最后更新**: 2026-04-11  
**制定人**: Leo  
**状态**: 已启用
