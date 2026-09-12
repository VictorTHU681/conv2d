"""Interleave independent ZA and vector accumulators within one KW step."""
import re


def interleaved(source, names):
    for name in names:
        start = source.index('static void ' + name + '(')
        end = source.index('\n}\n', start) + 3
        function = source[start:end]
        lo = function.index('        "2:\\n\\t"\n')
        hi = function.index('        "add x13,', lo)
        block = function[lo:hi]
        lines = block.splitlines(keepends=True)
        opa = [line for line in lines if '"fmopa ' in line]
        fma = [line for line in lines if '"fmla ' in line]
        # All loads precede arithmetic, including the one-row broadcast which
        # originally followed FMOPA. Nothing changes across KW iterations.
        loads = [line for line in lines if '"ld1' in line]
        assert len(opa) == 4 and len(fma) in (2, 6, 8)
        assert len(lines) == 1 + len(opa) + len(fma) + len(loads)
        reordered = [lines[0], *loads]
        for i, instruction in enumerate(opa):
            reordered.append(instruction)
            reordered.extend(fma[i * len(fma) // 4:(i + 1) * len(fma) // 4])
        new = ''.join(reordered)
        # No arithmetic instruction is added, removed or edited.
        assert sorted(re.findall(r'"([^"\n]*)"', block)) == sorted(re.findall(r'"([^"\n]*)"', new))
        function = function[:lo] + new + function[hi:]
        source = source[:start] + function + source[end:]
    return source
