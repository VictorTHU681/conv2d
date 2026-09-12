#!/usr/bin/env python3
"""Select the three-fold COPY4 kernel by residual-group structure, never exact test shape."""
from pathlib import Path
import hashlib, subprocess
subprocess.run(['python3', 'tools/gen_v56_fold_copy.py'], check=True, stdout=subprocess.DEVNULL)
prior = Path('build/v56/experiments/fold-copy')
base = (prior/'baseline.c').read_text()
nf3 = (prior/'nf3.c').read_text()
def selective(name):
    candidate = (prior/(name+'.c')).read_text()
    a = candidate.index('static void k16pairf3(')
    b = candidate.index('\n}\n', a) + 3
    clone = candidate[a:b].replace('k16pairf3(', 'k16pairf3_copy(')
    a = nf3.index('static void k16pairf3(')
    s = nf3[:a] + clone + '\n' + nf3[a:]
    old = 'else if (g->kind == 34) k16pairf3(&K);'
    new = 'else if (g->kind == 34) {\n            // Whole 32-row pairs plus seven residuals: fold three and fill K4.\n            // Plans with an additional single-16 group retain the original copier.\n            if (KH % 32 == 7) k16pairf3_copy(&K); else k16pairf3(&K);\n        }'
    assert s.count(old) == 1
    return s.replace(old, new)
root = Path('build/v56/experiments/fold-select')
root.mkdir(parents=True, exist_ok=True)
for name, s in [('baseline', base), ('nf3', nf3), ('selectcopy', selective('f3copy')), ('select128', selective('f3copy128'))]:
    p = root/(name+'.c'); p.write_text(s)
    print(hashlib.sha256(s.encode()).hexdigest(), p)
