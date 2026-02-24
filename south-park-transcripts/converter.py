"""Converter for South Park transcript HTML to Fountain format."""

import re
import html


def convert_to_fountain(html_content: str, episode_title: str = "") -> str:
    """Convert transcript HTML to Fountain format."""
    
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
    
    if pre_start == -1:
        return ""
    
    # Remove pre tags
    text = re.sub(r'</?pre[^>]*>', '', text, flags=re.IGNORECASE)
    
    # Remove <b> tags and unescape HTML entities
    text = re.sub(r'</?b>', '', text)
    text = html.unescape(text)
    
    # Remove any remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    lines = text.split('\n')
    fountain_lines = []
    
    # Skip header lines - find first actual dialogue
    start_idx = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Skip HTML/script tags and empty lines
        if stripped and not stripped.startswith(('<', '//', 'if ')) and len(stripped) > 0:
            if i < 20:  # In first 20 lines
                start_idx = max(0, i - 1)
                break
    
    if start_idx > 0:
        lines = lines[start_idx:]
    
    for line in lines:
        stripped = line.strip()
        
        if not stripped:
            fountain_lines.append("")
            continue
        
        # Check for scene heading
        scene_match = re.match(r'^(INT|EXT|I/E|INT/EXT)\.?\s+', stripped, re.IGNORECASE)
        if scene_match:
            fountain_lines.append(stripped.upper())
            continue
        
        # Check for character dialogue (usually in UPPERCASE followed by dialogue)
        # South Park format: CHARACTER: dialogue or CHARACTER
        #                             dialogue
        
        # Check if line is a character name (UPPERCASE, possibly with parentheses)
        # Character names are typically followed by dialogue
        leading_whitespace = len(line) - len(line.lstrip())
        
        # Character cue: indented 4+ spaces, all caps, contains letters
        if leading_whitespace >= 4 and stripped.isupper():
            # Check if it looks like a character name (no colons, reasonable length)
            if ':' not in stripped and len(stripped) < 40:
                fountain_lines.append(stripped)
                continue
        
        # Dialogue after character (indented less than character, or with colon)
        if ':' in stripped:
            parts = stripped.split(':', 1)
            if parts[0].strip().isupper() and len(parts[0].strip()) < 40:
                fountain_lines.append(parts[0].strip())
                if len(parts) > 1 and parts[1].strip():
                    fountain_lines.append(parts[1].strip())
                continue
        
        # Transition lines (FADE IN, CUT TO, etc.)
        if stripped.isupper() and any(t in stripped for t in ['FADE', 'CUT TO', 'DISSOLVE', 'SMASH CUT']):
            fountain_lines.append("> " + stripped)
            continue
        
        # Default: action/description
        fountain_lines.append(stripped)
    
    output = "\n".join(fountain_lines)
    # Remove excessive blank lines
    output = re.sub(r'\n{3,}', '\n\n', output)
    
    return output.strip()


def convert_html_to_fountain(html_content: str, episode_title: str = "") -> str:
    """Convenience function to convert HTML to Fountain."""
    return convert_to_fountain(html_content, episode_title)


if __name__ == "__main__":
    # Test with a file
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            html_content = f.read()
        fountain = convert_to_fountain(html_content)
        print(fountain)
