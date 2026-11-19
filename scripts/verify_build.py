#!/usr/bin/env python3
"""Conservative source and APK checks. This does not establish flash safety."""
from pathlib import Path
from zipfile import ZipFile
from hashlib import sha256
import json, re, sys, difflib

R = Path('verification'); R.mkdir(exist_ok=True)
B = R/'res-before'; A = Path('decoded/res')
old = {p.relative_to(B):p for p in B.rglob('*') if p.is_file()}
new = {p.relative_to(A):p for p in A.rglob('*') if p.is_file()}
issues = []
if old.keys() != new.keys():
    issues.append(f'Decoded resource filenames differ: {len(old.keys()-new.keys())} missing, {len(new.keys()-old.keys())} extra')
changed=[]
pat = re.compile(r'(<string\b[^>]*\bname="(?:system_error_manufacturer|system_error_wipe_data)"[^>]*>)(.*?)(</string>)', re.S)
for rel in sorted(old.keys() & new.keys()):
    a,b=old[rel].read_bytes(),new[rel].read_bytes()
    if a==b: continue
    changed.append(str(rel))
    if rel.as_posix() != 'values/strings.xml':
        issues.append(f'Unexpected source edit: {rel}')
        continue
    original=a.decode('utf-8'); modified=b.decode('utf-8')
    expected=pat.sub(lambda m: m.group(1)+m.group(3) if 'internal problem with your device' in m.group(2) else m.group(0), original)
    if expected != modified: issues.append('Unexpected change in values/strings.xml')
if changed != ['values/strings.xml']:
    issues.append(f'Expected only values/strings.xml changed, got: {changed}')
(R/'patched-files.txt').write_text('\n'.join(changed)+'\n')
original=Path('framework-res.apk'); rebuilt=Path('output/framework-res-modified.apk')
if rebuilt.exists():
    with ZipFile(original) as z1, ZipFile(rebuilt) as z2:
        n1={n for n in z1.namelist() if not n.startswith('META-INF/')}
        n2={n for n in z2.namelist() if not n.startswith('META-INF/')}
        missing=sorted(n1-n2); added=sorted(n2-n1)
        (R/'missing-paths.txt').write_text('\n'.join(missing)+'\n')
        (R/'extra-paths.txt').write_text('\n'.join(added)+'\n')
        if missing or added: issues.append(f'ZIP entry paths changed: {len(missing)} missing, {len(added)} added')
        hashes={}
        for label,z in [('original',z1),('rebuilt',z2)]:
            hashes[label]={n:sha256(z.read(n)).hexdigest() for n in ('resources.arsc','AndroidManifest.xml') if n in z.namelist()}
        (R/'critical-file-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
        if 'resources.arsc' not in hashes['rebuilt']: issues.append('Rebuilt APK missing resources.arsc')
        if 'AndroidManifest.xml' not in hashes['rebuilt']: issues.append('Rebuilt APK missing AndroidManifest.xml')
        # Hashes are diagnostic: resources.arsc is expected to change when strings are rebuilt.
else:
    print('Source-only check; APK not built yet')
(R/'verification-result.txt').write_text(('FAIL\n'+'\n'.join(issues) if issues else 'PASS')+'\n')
for issue in issues: print('ERROR:',issue,file=sys.stderr)
if issues: sys.exit(1)
print('Checks passed. APK remains unsigned and NOT validated for flashing.')
