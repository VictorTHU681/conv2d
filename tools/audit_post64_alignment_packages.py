#!/usr/bin/env python3
"""Verify exact upstream/candidate archives and all six four-shape full references."""
from pathlib import Path
import re,hashlib,zipfile
root=Path('results/post64/package-check');s=(root/'production.log').read_text()
assert 'POST64_PACKAGES_DONE' in s and 'FAIL' not in s
names=[(v,n) for v in ['upstream','aligned'] for n in ['conv','conv_nf3','conv_diag']]
assert re.findall(r'^ARCHIVE_BEGIN variant=(\w+) archive=(\w+) ',s,re.M)==names
assert re.findall(r'^ARCHIVE_PASS variant=(\w+) archive=(\w+)$',s,re.M)==names
manifest=(root/'archives.sha256').read_text().splitlines();assert len(manifest)==6
shapes=[(4096,6144,39,39),(6144,4096,41,41),(4256,6390,55,55),(6390,4256,81,81)]
for (v,n),line in zip(names,manifest):
 h,path=line.split();p=Path(path)
 assert p==Path('build/post64/package-check')/v/'submissions'/f'{n}.zip'
 assert hashlib.sha256(p.read_bytes()).hexdigest()==h
 assert re.search(r'^'+h+r'\s+'+re.escape(path)+r'$',s,re.M)
 block=s.split(f'ARCHIVE_BEGIN variant={v} archive={n} ')[1].split(f'ARCHIVE_PASS variant={v} archive={n}')[0]
 with zipfile.ZipFile(p) as z:
  assert len(z.namelist())==4 and set(z.namelist())=={'conv/README.md','conv/bench_conv.c','conv/conv2d.c','conv/run.sh'}
  sh=hashlib.sha256(z.read('conv/conv2d.c')).hexdigest()
  assert re.search(r'^'+sh+r'\s+/tmp/conv-post64-package\.[^/]+/'+v+'/'+n+r'/conv/conv2d.c$',block,re.M)
 rows=re.findall(r'^\s*(\d+)\s*x\s*(\d+)\s+(\d+)\s*x\s*(\d+)\s+([\d.]+)\s+([\d.]+)\s+(\S+)\s+(PASS|FAIL)\s*$',block,re.M)
 assert [tuple(map(int,r[:4])) for r in rows]==shapes
 assert all(float(r[6])==0 and r[7]=='PASS' for r in rows)
 print(f'{v}/{n}: exact archive/source identity and four original full-reference checks PASS; max error zero.')
print('24 original full-reference checks passed. Package timing is not comparative performance evidence; pending source acceptance is separate.')
