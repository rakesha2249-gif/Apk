from pathlib import Path
import re, sys
root=Path('decoded/res')
needle="There's an internal problem with your device"
changed=0
for path in root.glob('values*/strings.xml'):
    content=path.read_text(encoding='utf-8')
    # Keep the resource name and attributes intact; replace only the targeted string's text.
    pattern=re.compile(r'(<string\b[^>]*>)([^<]*)(</string>)')
    def replace(m):
        global changed
        if needle in m.group(2) or needle.replace("'", "\\'") in m.group(2) or 'There\\\'s an internal problem with your device' in m.group(2):
            changed+=1
            print('Matched:', path, m.group(1))
            return m.group(1)+m.group(3)
        return m.group(0)
    new=pattern.sub(replace,content)
    if new!=content: path.write_text(new,encoding='utf-8')
print('Changed string entries:',changed)
if changed==0:
    sys.exit('Target string not found. Build stopped without changes.')
  
