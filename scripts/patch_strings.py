#!/usr/bin/env python3
"""Blank only two specified system error string resources."""
from pathlib import Path
import re
import sys

ROOT = Path('decoded/res')
TARGETS = {'system_error_manufacturer', 'system_error_wipe_data'}
pattern = re.compile(r'(<string\b[^>]*\bname="(system_error_manufacturer|system_error_wipe_data)"[^>]*>)(.*?)(</string>)', re.DOTALL)
changes = []
for file in sorted(ROOT.glob('values*/strings.xml')):
    before = file.read_text(encoding='utf-8')
    names = []
    def replace(match):
        if 'There' not in match.group(3) or 'internal problem with your device' not in match.group(3):
            raise RuntimeError(f'Unexpected value for {match.group(2)} in {file}')
        names.append(match.group(2))
        return match.group(1) + '' + match.group(4)
    after = pattern.sub(replace, before)
    if names:
        if set(names) != TARGETS or len(names) != 2:
            raise RuntimeError(f'Incomplete/duplicate target strings in {file}: {names}')
        file.write_text(after, encoding='utf-8')
        changes.append(str(file))
if not changes:
    sys.exit('ERROR: No target strings found; refusing to build')
print('Patched only the two target string names in:')
print('\n'.join(changes))
