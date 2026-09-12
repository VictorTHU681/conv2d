Source: 54dc05d, SHA-256 `695c449ccdc0b234ae16812a49b26afc7a7d0153d5d0b33983c7b3a281f3530b`.

Host diagnostic uses the source grouping and resume_claim functions unchanged.
Two synthetic independent pieces span the same output rows in adjacent last strips.
Both can be claimed before either publishes completion. This demonstrates missing
cross-item exclusion, not a measured simultaneous SME store or an incorrect result.

| KH | Kind | Strip width | Penultimate columns | Final columns | Shared columns | Claim state |
| --- | --- | ---: | --- | --- | ---: | --- |
| 39 | 35 | 32 | [6048,6080) | [6074,6106) | 6 | both busy |
| 39 | 4 | 256 | [5632,5888) | [5850,6106) | 38 | both busy |
| 41 | 33 | 32 | [4000,4032) | [4024,4056) | 8 | both busy |
| 41 | 8 | 128 | [3840,3968) | [3928,4056) | 40 | both busy |
| 55 | 4 | 256 | [5888,6144) | [6080,6336) | 64 | both busy |
| 81 | 35 | 32 | [4128,4160) | [4144,4176) | 16 | both busy |
| 81 | 35 | 32 | [4128,4160) | [4144,4176) | 16 | both busy |
| 81 | 9 | 128 | [3968,4096) | [4048,4176) | 48 | both busy |
