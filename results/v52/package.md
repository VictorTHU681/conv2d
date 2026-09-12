# v52 submission archive acceptance

Job `1579584`, cn20481, 2026-09-12 18:11:28–18:12:13 +08:00.
`jobs/v52_zip_job.sh` extracted the actual archive into a fresh temporary
directory, checked source/benchmark/entry-point equality, ran `bash run.sh`,
then compiled the packing-reuse regression against the extracted source.
Complete raw output: `zip.log`.

- Archive: `submissions/conv.zip`, eight files beneath `conv/`.
- Archive SHA-256:
  `917e9c8b7cc01716d216ac8c45da22416b3a263195f1ef81137ec8effa59f6d4`
- Source SHA-256:
  `aedf54a51dd925eadc79a6e4a653c3e66935783c890b7afe43c0cfcbc3cb61fa`

The unchanged submission entry point selected NUMA5 + HBM21 and 38 threads.
All four full-reference checks passed with maximum absolute error zero:

| Kernel | GFLOPS |
|---|---:|
| 39 | 14258.4657 |
| 41 | 14201.5320 |
| 55 | 14538.2637 |
| 81 | 14590.6214 |

These single entry-point timings verify the package. The five-round performance
comparison against v51 used NUMA1 + HBM17 and is documented in `docs/v52.md`;
do not compare the two placements as an algorithmic improvement.

The extracted source also passed all 32 signed bitwise kernel-switch calls on
NUMA1 + HBM17. After the first 81/39/39/55 cycle there were zero new aligned
allocations, with peak tracked aligned storage of 12 MiB.

This record and the raw logs are stored outside the archive, preserving the
exact bytes of the accepted submission package.
