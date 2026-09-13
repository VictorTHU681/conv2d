14 complete diagnostic calls and 10 timed hashes PASS. Each call totals 135448 K5 rows, matching independently profiled tile work.
Counts are from a separate instrumented executable. They describe observed geometry, not the allocation alignment of every uninstrumented timing process; diagnostic timings are not used for acceptance.

| Memory | Tail triples | Scalars | Calls summed | Rows summed | Row share |
| --- | ---: | ---: | ---: | ---: | ---: |
| DDR | 1 | 1 | 525 | 43008 | 4.54% |
| DDR | 14 | 2 | 11074 | 905128 | 95.46% |

DDR: empty vector tail 0.00% of observed K5 rows.

| HBM | 1 | 1 | 525 | 43008 | 4.54% |
| HBM | 14 | 2 | 11074 | 905128 | 95.46% |

HBM: empty vector tail 0.00% of observed K5 rows.

