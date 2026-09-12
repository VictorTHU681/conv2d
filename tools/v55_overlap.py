"""Overlap next-row ring copies with the first KW arithmetic iterations."""


def line(instruction):
    return '        "' + instruction + '\\n\\t"\n'


def overlap(source, names):
    head = ['add x21, x0, x26', 'ldr x12, [%[A], #240]',
            'add x16, x17, x12', 'sub x17, x28, x17',
            'add x22, x0, x1', 'cmp x8, #1', 'csel x22, x0, x22, eq',
            'mov x23, x17', 'ldr x12, [%[A], #168]']
    copy = ['prfm pldl2keep, [x21]', 'ld1w {z24.s}, p0/z, [x22]',
            'st1w {z24.s}, p0, [x23]', 'add x21, x21, #64',
            'add x22, x22, #64', 'add x23, x23, #64', 'sub x12, x12, #1']
    tail = ['prfm pldl2keep, [x21]', 'ld1w {z24.s}, p3/z, [x22]',
            'st1w {z24.s}, p3, [x23]']
    emit = lambda instructions: ''.join(map(line, instructions))
    for name in names:
        lo = source.index('static void ' + name + '(')
        hi = source.index('\n}\n', lo) + 3
        function = source[lo:hi]
        start = function.index('        ROW_HEAD_')
        body_start = function.index(line('2:'), start) + len(line('2:'))
        body_end = function.index(line('subs x15, x15, #1'), body_start)
        body = function[body_start:body_end]
        end = function.index('        WRAP_B(', body_end)
        assert 'x12' not in body and 'z24' not in body
        assert '"z24"' in function
        alignment = ['.p2align 4'] if '.p2align 4' in function[start:body_start] else []
        # At most one copy accompanies each arithmetic step. If KW is short,
        # finish remaining full copies afterward, then execute the tail copy.
        # Long KW: copy the tail once, then use the unchanged pure-FMA loop.
        replacement = (emit(head + ['mov x15, x7', 'cbz x12, 71f', '70:']) +
                       emit(copy) + body +
                       emit(['subs x15, x15, #1', 'b.eq 73f', 'cbnz x12, 70b', '71:']) +
                       emit(tail + alignment + ['2:']) + body +
                       emit(['subs x15, x15, #1', 'b.ne 2b', 'b 74f', '73:',
                             'cbz x12, 72f', '75:']) +
                       emit(copy + ['cbnz x12, 75b', '72:']) + emit(tail + ['74:']))
        function = function[:start] + replacement + function[end:]
        source = source[:lo] + function + source[hi:]
    return source
