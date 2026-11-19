from pathlib import Path
import re
path=Path('decoded/res/values/strings.xml')
text=path.read_text(encoding='utf-8')
for name in ('system_error_manufacturer','system_error_wipe_data'):
    pattern=re.compile(r'(<string\b[^>]*\bname=["\']'+re.escape(name)+r'["\'][^>]*>)(.*?)(</string>)',re.S)
    matches=list(pattern.finditer(text))
    if len(matches)!=1: raise RuntimeError(f'Expected exactly one {name}, found {len(matches)}')
    text=pattern.sub(lambda m:m.group(1)+m.group(3),text,count=1)
path.write_text(text,encoding='utf-8')
print('Two English strings cleared')
