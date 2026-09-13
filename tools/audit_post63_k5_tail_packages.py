#!/usr/bin/env python3
"""Check exact archive identities and all original full-reference results."""
from pathlib import Path
import hashlib,re,zipfile
root=Path('results/post63/k5-tail')
s=(root/'packages.log').read_text()
assert 'K5_TAIL_ZIP_DONE' in s and 'FAIL' not in s
names=['conv','conv_nf3','conv_diag']
assert re.findall(r'^ARCHIVE_BEGIN (\w+) ',s,re.M)==names
assert re.findall(r'^ARCHIVE_PASS (\w+)$',s,re.M)==names
for line in (root/'packages_candidate.sha256').read_text().splitlines():
    h,path=line.split();p=Path(path)
    assert hashlib.sha256(p.read_bytes()).hexdigest()==h
    assert re.search(r'^'+h+r'\s+'+re.escape(path)+r'$',s,re.M)
    with zipfile.ZipFile(p) as z:
        assert len(z.namelist())==4 and set(z.namelist())=={'conv/conv2d.c','conv/bench_conv.c','conv/run.sh','conv/README.md'}
        sh=hashlib.sha256(z.read('conv/conv2d.c')).hexdigest()
        assert re.search(r'^'+sh+r'\s+/tmp/conv-post63-archive\.[^/]+/'+p.stem+r'/conv/conv2d.c$',s,re.M)
expected=[(4096,6144,39,39),(6144,4096,41,41),(4256,6390,55,55),(6390,4256,81,81)]
for name in names:
    block=s.split('ARCHIVE_BEGIN '+name+' ')[1].split('ARCHIVE_PASS '+name)[0]
    rows=re.findall(r'^\s*(\d+)\s*x\s*(\d+)\s+(\d+)\s*x\s*(\d+)\s+([\d.]+)\s+([\d.]+)\s+(\S+)\s+(PASS|FAIL)\s*$',block,re.M)
    assert [tuple(map(int,row[:4])) for row in rows]==expected
    assert all(float(row[6])==0 and row[7]=='PASS' for row in rows)
    print(f'{name}: exact archive and source hashes match; four original full-reference checks PASS, maximum errors zero.')
print('Job 1590008, cn20490: 12 full checks passed for the v62 scalar-tail-unrolled candidate. This does not itself establish comparative performance.')
