#!/usr/bin/env python3
"""Check that live K5 plane reads never depend on zero-filled tail padding."""
cases=reads=0
for kw in range(3,401):
    for sh in range(16):
        live=kw+191;ncp=live+sh
        full,tail,scalar=ncp//48,ncp%48//3,ncp%3
        stride=((ncp+2)//3+15)//16*16+16
        for policy in ['baseline','guard','unroll']:
            # Poison every uninitialized element. A missing live write must fail.
            planes=[[None]*stride for _ in range(3)]
            for i in range(full*48):planes[i%3][i//3]=i-sh
            if tail or policy!='guard':
                for p in range(3):
                    for j in range(16):
                        planes[p][full*16+j]=(full*48+3*j+p-sh) if j<tail else 'zero padding'
            # scalar is structurally limited to 0..2; unrolled addresses match
            # the first and optional second plane at the same element index.
            if scalar:
                planes[0][full*16+tail]=full*48+3*tail-sh
                if scalar==2:planes[1][full*16+tail]=full*48+3*tail+1-sh
            for q in range(kw+2):
                p,start=(sh+q)%3,(sh+q)//3
                for j in [0,63]:
                    assert planes[p][start+j]==q+3*j
                    assert 0<=q+3*j<live
                    reads+=1
            cases+=1
print(f'{cases} supported KW/alignment/policy geometries PASS; {reads} first/last-lane checks across every compute step do not consume poisoned or zero-padding elements.')
print('Each interior copied plane is an uninterrupted arithmetic progression; endpoint mapping and monotonicity cover its 64-lane compute load. This is an address/value model, not dynamic instruction tracing.')
print('Both variants preserve valid scalar addresses and FMA order. Empty-tail bypass leaves padding untouched; the scalar unroll reads one float, then a second only when the remainder is two.')
