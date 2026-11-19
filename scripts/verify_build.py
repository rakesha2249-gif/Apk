#!/usr/bin/env python3
"""Fail on unexpected source edits or changed ZIP entry paths (signatures excluded)."""
from pathlib import Path
from zipfile import ZipFile
import difflib
import re
import sys

before = Path('verification/res-before')
after = Path('decoded/res')
report = Path('verification')
report.mkdir(exist_ok=True)
old_files = {p.relative_to(before) for p in before.rglob('*') if p.is_file()}
new_files = {p.relative_to(after) for p in after.rglob('*') if p.is_file()}
errors = []
if old_files != new_files:
    errors.append('Decoded resource filenames changed')
allowed = {'system_error_manufacturer', 'system_error_wipe_data'}
pattern = re.compile(r'(<string\b[^>]*\bname="(system_error_manufacturer|system_error_wipe_data)"[^>]*>)(.*?)(</string>)', re.DOTALL)
changed = []
for rel in sorted(old_files & new_files):
    old = (before / rel).read_bytes()
    new = (after / rel).read_bytes()
    if old == new:
        continue
    if not (rel.name == 'strings.xml' and rel.parent.name.startswith('values')):
        errors.append(f'Unexpected edited resource: {rel}')
        continue
    a, b = old.decode('utf-8'), new.decode('utf-8')
    def blank(m):
        if 'internal problem with your device' not in m.group(3):
            return m.group(0)
        return m.group(1) + m.group(4)
    if pattern.sub(blank, a) != b:
        errors.append(f'Unexpected XML change: {rel}')
    else:
        changed.append(str(rel))
if not changed:
    errors.append('No expected strings were changed')
(report / 'patched-files.txt').write_text('\n'.join(changed) + '\n')

original = Path('framework-res.apk')
modified = Path('output/framework-res-modified.apk')
if modified.exists():
    with ZipFile(original) as z:
        original_names = set(z.namelist())
    with ZipFile(modified) as z:
        modified_names = set(z.namelist())
    # The original signature cannot remain valid after modification.
    def unsigned_entries(names):
        return {n for n in names if not n.startswith('META-INF/')}
    missing = sorted(unsigned_entries(original_names) - unsigned_entries(modified_names))
    extra = sorted(unsigned_entries(modified_names) - unsigned_entries(original_names))
    (report / 'missing-paths.txt').write_text('\n'.join(missing) + '\n')
    (report / 'extra-paths.txt').write_text('\n'.join(extra) + '\n')
    if missing or extra:
        errors.append(f'APK resource paths differ: {len(missing)} missing, {len(extra)} added')
else:
    print('Source-only verification (APK not built yet)')
(report / 'verification-result.txt').write_text('PASS\n' if not errors else 'FAIL\n' + '\n'.join(errors) + '\n')
if errors:
    print('\n'.join('ERROR: ' + e for e in errors), file=sys.stderr)
    sys.exit(1)
print('Verification passed; NOTE: rebuilt APK is unsigned and not flash-ready')
