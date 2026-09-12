"""Reuse one step's input vectors for the following FMA step, preserving order."""
def shifted(source, names, ext=True):
    def line(s): return '        "'+s+'\\n\\t"\n'
    for name in names:
        a=source.index('static void '+name+'(');b=source.index('\n}\n',a)+3
        f=source[a:b];label=line('2:');start=f.index(label)
        stop=f.index(line('subs x15, x15, #1'),start)
        body=f[start+len(label):stop]
        count=4 if name=='k16single' else 2
        input_loads=[line('ld1w {z0.s}, p0/z, [x16]')]
        input_loads += [line(f'ld1w {{z{i}.s}}, p0/z, [x16, #{i}, mul vl]') for i in range(1,count)]
        if ext:
            for l in input_loads: assert body.count(l)==1
            nextbody=body
            for l in input_loads: nextbody=nextbody.replace(l,'')
            shifts=''.join(line(f'ext z{i}.b, z{i}.b, z{i+1 if i+1<count else 18}.b, #4') for i in range(count))
            repeated=line(f'ld1w {{z18.s}}, p0/z, [x16, #{count}, mul vl]')+body+shifts+nextbody
            f=f.replace(': XCLOB,', ': XCLOB, "z18",')
        else: repeated=body+body
        tail=line('subs x15, x15, #1')+line('b.ne 2b')
        old=label+body+tail;assert f.count(old)==1
        new=(line('lsr x15, x7, #1')+line('cbz x15, 43f')+label+repeated+tail+
             line('43:')+line('tbz x7, #0, 44f')+body+line('44:'))
        f=f.replace(old,new);source=source[:a]+f+source[b:]
    return source
