"""Use non-temporal source-load hints while keeping ring stores temporal."""


def non_temporal_copy(source, pair4_only=False):
    start = source.index('#define ROW_HEAD_COPY4' if pair4_only else '#define ROW_HEAD_COMMON')
    end = source.index('// ---------------- 4×4：', start)
    part = source[start:end]
    # Scalar-base contiguous LDNT1W has the same addresses/predicates here.
    # Z24 is the ring-copy scratch register; arithmetic input loads stay LD1W.
    count = part.count('ld1w {z24.s}')
    assert count >= (6 if pair4_only else 8), count
    part = part.replace('ld1w {z24.s}', 'ldnt1w {z24.s}')
    return source[:start] + part + source[end:]
