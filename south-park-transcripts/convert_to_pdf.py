"""Convert South Park Fountain transcripts to PDF.

This script converts existing .fountain files to .pdf files.
Run after 01 and 02 are complete.
"""

import os
import re
from pathlib import Path

from weasyprint import HTML, CSS

# Configuration
TRANSCRIPTS_DIR = Path(__file__).parent / "transcripts"


# Screenplay CSS for PDF
SCREENPLAY_CSS = """
@page {
    size: letter;
    margin: 1in;
}

body {
    font-family: Courier, monospace;
    font-size: 12pt;
    line-height: 1.0;
    margin: 0;
    padding: 0;
}

.title-header {
    text-align: center;
    margin-bottom: 1in;
}

.title-header h1 {
    font-size: 24pt;
    font-weight: bold;
    margin: 0;
    text-transform: uppercase;
}

.scene-heading {
    font-weight: bold;
    text-transform: uppercase;
    margin-top: 1em;
    margin-bottom: 0.5em;
}

.action {
    margin-bottom: 0.5em;
}

.character {
    margin-left: 2in;
    margin-top: 0.5em;
    font-weight: bold;
}

.dialogue {
    margin-left: 1.5in;
    margin-right: 2in;
    margin-bottom: 0.5em;
}

.parenthetical {
    margin-left: 1.75in;
    margin-right: 2in;
}

.transition {
    text-align: right;
    text-transform: uppercase;
    margin-top: 0.5em;
    margin-bottom: 0.5em;
}

.centered {
    text-align: center;
}
"""


def parse_fountain(content: str) -> list:
    """Simple fountain parser."""
    elements = []
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        
        # Skip empty lines at start
        if not line.strip():
            i += 1
            continue
        
        # Title (first occurrence)
        if line.lower().startswith('title:'):
            title = line.split(':', 1)[1].strip()
            elements.append({'type': 'title', 'text': title})
            i += 1
            continue
        
        # Scene heading (INT., EXT., etc.)
        if re.match(r'^(INT|EXT|I/E|INT/EXT)\.?\s+', line, re.IGNORECASE):
            elements.append({'type': 'scene_heading', 'text': line})
            i += 1
            continue
        
        # Transition (FADE IN, CUT TO, etc.) - right aligned
        if line.isupper() and ('FADE' in line or 'CUT TO' in line or 'DISSOLVE' in line or 'SMASH CUT' in line):
            elements.append({'type': 'transition', 'text': line})
            i += 1
            continue
        
        # Transition with >
        if line.startswith('>'):
            elements.append({'type': 'transition', 'text': line[1:].strip()})
            i += 1
            continue
        
        # Character - line is all caps and followed by dialogue
        if line.isupper() and len(line) < 40 and not line.startswith('('):
            # Check if next non-empty line is not all caps (dialogue)
            next_idx = i + 1
            while next_idx < len(lines) and not lines[next_idx].strip():
                next_idx += 1
            
            if next_idx < len(lines):
                next_line = lines[next_idx].strip()
                # If next line is not all caps or is indented, it's dialogue
                if not next_line.isupper() or next_line.startswith('('):
                    elements.append({'type': 'character', 'text': line})
                    i += 1
                    continue
        
        # Parenthetical
        if line.startswith('(') and line.endswith(')'):
            elements.append({'type': 'parenthetical', 'text': line})
            i += 1
            continue
        
        # Default: action/dialogue
        # Check indentation
        indent = len(line) - len(line.lstrip())
        if indent >= 20:
            # Character name (less common format)
            elements.append({'type': 'character', 'text': line.strip()})
        elif indent >= 10:
            # Dialogue
            elements.append({'type': 'dialogue', 'text': line.strip()})
        else:
            # Action
            elements.append({'type': 'action', 'text': line.strip()})
        
        i += 1
    
    return elements


def fountain_to_html(fountain_content: str, title: str = "") -> str:
    """Convert fountain content to HTML."""
    # Parse fountain
    elements = parse_fountain(fountain_content)
    
    # Extract title from elements if not provided
    if not title:
        for elem in elements:
            if elem.get('type') == 'title':
                title = elem.get('text', '')
                break
    
    # Build HTML
    html_parts = ['<html><head><meta charset="utf-8"></head><body>']
    
    # Title header
    if title:
        html_parts.append(f'<div class="title-header"><h1>{title}</h1></div>')
    
    for elem in elements:
        if elem.get('type') == 'scene_heading':
            html_parts.append(f'<div class="scene-heading">{elem.get("text", "")}</div>')
        elif elem.get('type') == 'action':
            html_parts.append(f'<div class="action">{elem.get("text", "")}</div>')
        elif elem.get('type') == 'character':
            html_parts.append(f'<div class="character">{elem.get("text", "")}</div>')
        elif elem.get('type') == 'dialogue':
            html_parts.append(f'<div class="dialogue">{elem.get("text", "")}</div>')
        elif elem.get('type') == 'parenthetical':
            html_parts.append(f'<div class="parenthetical">{elem.get("text", "")}</div>')
        elif elem.get('type') == 'transition':
            html_parts.append(f'<div class="transition">{elem.get("text", "")}</div>')
        elif elem.get('type') == 'centered':
            html_parts.append(f'<div class="centered">{elem.get("text", "")}</div>')
        elif elem.get('type') == 'title':
            pass  # Already displayed in header
    
    html_parts.append('</body></html>')
    return '\n'.join(html_parts)


def convert_fountain_to_pdf(fountain_path: Path, output_path: Path) -> bool:
    """Convert a single fountain file to PDF."""
    try:
        # Read fountain content
        with open(fountain_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract title from fountain (first Title line or use filename)
        title = ""
        for line in content.split('\n'):
            if line.strip().lower().startswith('title:'):
                title = line.split(':', 1)[1].strip()
                break
        
        if not title:
            # Use filename as title (remove episode code)
            title = fountain_path.stem
            # Remove season/episode prefix if present
            title = re.sub(r'^S\d+E\d+_', '', title)
            title = title.replace('_', ' ')
        
        # Convert to HTML
        html_content = fountain_to_html(content, title)
        
        # Convert to PDF using WeasyPrint
        html = HTML(string=html_content)
        html.write_pdf(output_path, stylesheets=[CSS(string=SCREENPLAY_CSS)])
        
        return True
    
    except Exception as e:
        print(f"Error converting {fountain_path.name}: {e}")
        return False


def main():
    """Main entry point."""
    print("=" * 60)
    print("South Park Fountain to PDF Converter")
    print("=" * 60)
    
    # Find all fountain files
    fountain_files = list(TRANSCRIPTS_DIR.glob("*.fountain"))
    
    if not fountain_files:
        print(f"No .fountain files found in {TRANSCRIPTS_DIR}")
        return
    
    print(f"\nFound {len(fountain_files)} fountain files")
    
    # Convert each file
    successful = 0
    failed = 0
    skipped = 0
    
    for i, fountain_file in enumerate(fountain_files):
        # Output filename
        pdf_file = fountain_file.with_suffix('.pdf')
        
        # Skip if PDF already exists
        if pdf_file.exists():
            print(f"  [{i+1}/{len(fountain_files)}] {fountain_file.name} → Already exists, skipping")
            skipped += 1
            continue
        
        print(f"  [{i+1}/{len(fountain_files)}] {fountain_file.name} → {pdf_file.name}...", end=" ", flush=True)
        
        if convert_fountain_to_pdf(fountain_file, pdf_file):
            print("✓")
            successful += 1
        else:
            print("✗")
            failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print(f"  Total fountain files: {len(fountain_files)}")
    print(f"  Successfully converted: {successful}")
    print(f"  Skipped (already exists): {skipped}")
    print(f"  Failed: {failed}")
    print(f"\nPDFs saved to: {TRANSCRIPTS_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
