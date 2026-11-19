#!/usr/bin/env python3
"""Diagnostic comparison only; never certifies flash safety."""
from pathlib import Path
from zipfile import ZipFile
import hashlib, json, re, difflib

out=Path('verification'); out.mkdir(exist_ok=True)
a=Path('verification/res-before'); b=Path('decoded/res')
old={str(p.relative_to(a)):p for p in a.rglob('*') if p.is_file()}
new={str(p.relative_to(b)):p for p in b.rglob('*') if p.is_file()}
changed=[k for k in sorted(old.keys() & new.keys()) if old[k].read_bytes()!=new[k].read_bytes()]
(out/'source-changes.json').write_text(json.dumps({'changed':changed,'missing':sorted(old.keys()-new.keys()),'added':sorted(new.keys()-old.keys())},indent=2))
if changed != ['values/strings.xml'] or old.keys()!=new.keys():
    raise SystemExit('Unexpected decoded source changes; see source-changes.json')
orig=old['values/strings.xml'].read_text(); mod=new['values/strings.xml'].read_text()
pat=re.compile(r'(<string\b[^>]*\bname=["\'](?:system_error_manufacturer|system_error_wipe_data)["\'][^>]*>)(.*?)(</string>)',re.S)
expected,count=pat.subn(lambda m:m.group(1)+m.group(3),orig)
if count!=2 or mod!=expected:
    raise SystemExit('String changes are not exactly the two intended values')
print('Source verification passed')
rebuilt=Path('output/framework-res-modified.apk')
if not rebuilt.exists():
    exit(0)
with ZipFile('framework-res.apk') as x, ZipFile(rebuilt) as y:
    xnames=set(x.namelist()); ynames=set(y.namelist())
    oldnames={n for n in xnames if not n.startswith('META-INF/')}
    newnames={n for n in ynames if not n.startswith('META-INF/')}
    missing=sorted(oldnames-newnames); added=sorted(newnames-oldnames)
    def normalize(p):
        # Diagnostic grouping only: removes trailing Android version qualifier from directory.
        return re.sub(r'-v\d+(?=/)', '', p)
    added_by_norm={}
    for p in added: added_by_norm.setdefault(normalize(p),[]).append(p)
    pairs=[]; unmatched=[]
    for p in missing:
        candidates=added_by_norm.get(normalize(p),[])
        if len(candidates)==1:
            q=candidates.pop()
            pairs.append({'original':p,'rebuilt':q,'same_bytes':hashlib.sha256(x.read(p)).digest()==hashlib.sha256(y.read(q)).digest()})
        else: unmatched.append(p)
    unused=sorted(p for group in added_by_norm.values() for p in group)
    critical={}
    for name in ['resources.arsc','AndroidManifest.xml']:
        critical[name]={'original_sha256':hashlib.sha256(x.read(name)).hexdigest() if name in xnames else None,'rebuilt_sha256':hashlib.sha256(y.read(name)).hexdigest() if name in ynames else None}
    report={'missing_count':len(missing),'added_count':len(added),'normalized_pairs':len(pairs),'unmatched_missing':unmatched,'unmatched_added':unused,'mapped_examples':pairs[:50],'mapped_different_content_count':sum(not p['same_bytes'] for p in pairs),'critical':critical,'warning':'Path normalization is NOT proof that resources.arsc references are valid or that APK is safe to flash.'}
    (out/'apk-diagnostics.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'path-mappings.json').write_text(json.dumps(pairs,indent=2)+'\n')
    (out/'missing-paths.txt').write_text('\n'.join(missing)+'\n')
    (out/'added-paths.txt').write_text('\n'.join(added)+'\n')
    print(f'Path changes: {len(missing)} missing, {len(added)} added; mapped {len(pairs)}')
    if missing or added or critical['AndroidManifest.xml']['original_sha256']!=critical['AndroidManifest.xml']['rebuilt_sha256']:
        raise SystemExit('Diagnostic differences found. APK NOT approved for release or flashing.')
    raise SystemExit('No path differences, but signing and semantic validation still required. APK NOT approved for flashing.')
    
