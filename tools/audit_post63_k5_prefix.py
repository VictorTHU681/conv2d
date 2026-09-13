#!/usr/bin/env python3
"""Model interleaved, serial and tail copy partitions and plane endpoints."""
from collections import Counter
cases = 0
examples = {}
for kw in range(3,401):  # actual rolling-entry range
    live = kw+191
    for alignment in range(16):
        for policy in ['baseline','exact']:
            sh = alignment if policy=='baseline' else 0
            ncp = live+sh
            full, tail, scalar = ncp//48, ncp%48//3, ncp%3
            it, rem = (kw+2)//3, (kw+2)%3
            ovn = max(0,min(it-1,full))
            ovr = full-ovn
            assert it-ovn>=1 and ovn+ovr==full
            assert 3*it+rem==kw+2
            stride = ((ncp+2)//3+15)//16*16+16
            # Actual source segments: tail first, then serial supplement,
            # then one full block per interleaved compute iteration.
            intervals = [(full*48, full*48+3*tail)]
            intervals += [(full*48+3*tail+i,full*48+3*tail+i+1) for i in range(scalar)]
            intervals += [(48*b,48*(b+1)) for b in range(ovn,full)]
            intervals += [(48*b,48*(b+1)) for b in range(ovn)]
            cursor=0
            for lo,hi in sorted((lo,hi) for lo,hi in intervals if hi>lo):
                assert lo==cursor and hi<=ncp
                cursor=hi
            assert cursor==ncp and cursor-sh==live
            assert full*16+16<=stride  # unconditional vector tail stores
            for q in {0,1,2,kw-1,kw,kw+1}:
                plane,start=(sh+q)%3,(sh+q)//3
                for j in [0,63]:
                    x=3*(start+j)+plane-sh
                    assert x==q+3*j and 0<=x<live and start+j<stride
            cases+=1
            if kw in [3,4,5,41,400] and alignment in [0,8]:
                examples[kw,alignment,policy]=(sh,ovn,ovr,tail,scalar,it-ovn)
print(f'{cases} supported KW/alignment/policy geometries PASS; disjoint source segments cover exactly the required span, with at least one pure compute iteration.')
print('Model only, not dynamic proof of every assembly load/store. KW 1/2 do not enter rolling kernels. First-row initialization is separate; later copies read next row or repeat current final row.')
for key,value in sorted(examples.items()):
    print(f'KW/alignment/policy={key}: prefix/interleaved48/serial48/tail_triples/scalars/pure_iterations={value}')
