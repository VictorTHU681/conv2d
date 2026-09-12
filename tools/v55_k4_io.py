"""K4 controls: explicit permutations versus structured vector load/store."""


def macro_lines(instructions):
    return ''.join('        "' + ins + '\\n\\t" \\\n' for ins in instructions)


def k4_io(source, copy=False, output=False):
    if copy:
        lo = source.index('#define K4_CP(')
        hi = source.index('#define K4_STEP(', lo)
        macro = source[lo:hi]
        old = macro_lines(['ld4w {z0.s, z1.s, z2.s, z3.s}, p0/z, [x12]'])
        code = ['ld1w {z0.s}, p0/z, [x12]']
        code += [f'ld1w {{z{i}.s}}, p0/z, [x12, #{i}, mul vl]' for i in range(1, 4)]
        code += ['uzp1 z5.s, z0.s, z1.s', 'uzp2 z6.s, z0.s, z1.s',
                 'uzp1 z7.s, z2.s, z3.s', 'uzp2 z8.s, z2.s, z3.s',
                 'uzp1 z0.s, z5.s, z7.s', 'uzp1 z1.s, z6.s, z8.s',
                 'uzp2 z2.s, z5.s, z7.s', 'uzp2 z3.s, z6.s, z8.s']
        assert macro.count(old) == 1
        source = source[:lo] + macro.replace(old, macro_lines(code)) + source[hi:]
        # The predicated tail remains LD4W: separate contiguous tail loads
        # would require different predicates and bounds handling.
    if output:
        lo = source.index('#define K4_EV(')
        hi = source.index('static void k4(', lo)
        macro = source[lo:hi]
        old = '        "st4w {z0.s, z1.s, z2.s, z3.s}, p0, [x20, #4*" #T ", mul vl]\\n\\t" \\\n'
        code = ['zip1 z5.s, z0.s, z2.s', 'zip2 z7.s, z0.s, z2.s',
                'zip1 z6.s, z1.s, z3.s', 'zip2 z8.s, z1.s, z3.s',
                'zip1 z0.s, z5.s, z6.s', 'zip2 z1.s, z5.s, z6.s',
                'zip1 z2.s, z7.s, z8.s', 'zip2 z3.s, z7.s, z8.s']
        new = macro_lines(code)
        new += '        "add x13, x20, #256*" #T "\\n\\t" \\\n'
        new += macro_lines(['st1w {z0.s}, p0, [x13]'] + [
            f'st1w {{z{i}.s}}, p0, [x13, #{i}, mul vl]' for i in range(1, 4)])
        assert macro.count(old) == 1
        source = source[:lo] + macro.replace(old, new) + source[hi:]
    lo = source.index('static void k4(')
    hi = source.index('\n}\n', lo) + 3
    function = source[lo:hi]
    assert function.count(': XCLOB,') == 1
    function = function.replace(': XCLOB,', ': XCLOB, "z5", "z6", "z7", "z8",')
    return source[:lo] + function + source[hi:]
