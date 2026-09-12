# Larger early chunks with fine completion granularity

Baseline is accepted local v56 **8629457 / 1d3f5071…871a**. No push.
Earlier K5 profiling showed short chunks reduce the last-worker gap but increase
parameter and carry overhead. Transfer-width and restore-placement controls do
not improve throughput. These candidates test fewer early chunk boundaries.

Only actual prepared plans containing K5 and no explicit CONV_ROLL_STEP override
enable guidance. Other plans and every explicit override retain fixed behavior.
Base step remains 2*KH. grow2 uses 2*step while remaining rows exceed 4*step;
grow4 uses 4*step while remaining rows exceed 8*step. Near completion both return
to base step, with the final chunk clamped to remaining rows. No public complete
shape, memory-placement or call-stage selection is introduced.

One exact roll_chunk_rows helper determines both dependency wait ranges in
resume_claim and the executed worker range. Nonfinal chunks remain KH multiples,
so existing prepared phases remain valid. Input copy bounds, ZA/FMLA carry,
release publication, coefficient packing and FP32 kernels are unchanged. No
input/weight/result cache. Existing external concurrent-caller, allocation and
SVL limitations remain. Compiler layout also changes, so actual throughput must
be measured rather than inferred from the lower boundary count.

Host ASan/UBSan checks extract the candidates' actual types, grouping, dependency
builder, helper and claim code. Both pass **21,802 plans**: grow2 has 657,024 edges,
5,834,803 claims and 763,108 resumed claims; grow4 has 657,362 edges, 5,841,085
claims and 768,157 resumes. Checks cover grouping ownership, overlapping active
chunk rows, non-stuck completion and KH-aligned continuation offsets, across
KH16..256, width boundaries and step1..64. This simulation is finite and does not
execute SME instructions or prove all possible concurrent interleavings.

Screening job **1584781**, cn20481, started 06:46:30. Planned checks: both candidates
in five default-step signed state packing modes; separate explicit step1 override;
guards; standard output ownership; and long K5 ownership cases with actual large
and small chunk counters. The long diagnostic uses OMP=3, KH41/57/249, widths
193/257, output heights 4099/4113, and default/parallel packing, 48 cases across
two candidates. Counters are diagnostic-only and never used for timing. Default
sweeps must unset CONV_ROLL_STEP, otherwise they would disable the new policy.
Then six permutations, five timings/process, four shapes and separate DDR/HBM.
Planned 3,580 state/guard, 156 ownership cases, 720 timed hashes. Still running.

Profile job **1584806**, cn20483 06:47:50–06:48:39, succeeded. All six orders,
five timed calls/process for KH41 DDR/HBM: 36 processes, 9,576 phase records and
180 timed hashes validate. Saves equal resumes; every call processes 916,936
row work units and 186 pieces. [Profile summary](../../results/v56/experiments/guided-chunks/profile_summary.md).

Chunks per worker fall 295.3 -> 155.4 / 98.4. DDR restore/zero falls 45.6 ->
14.6 / 13.3 us; save/publish falls 53.5 -> 31.6 / 24.2 us. But the last-minus-mean
worker end gap rises 42.0 -> 79.7 / 128.8 us. Last completion is 5863.6 ->
5864.9 / 5951.5 us, so the measured savings do not improve DDR completion.
HBM last completion improves 5832.2 -> 5757.5 / 5765.4 us in this instrumented
run. Timers and layout perturb execution; no accepted end-to-end gain is inferred.
Screening 1584781 is still running and remains decisive before any next acceptance.
Root and archives unchanged.

## Matched-binary follow-up

Job **1584858**, cn20483, is submitted using one grow2 instrumented binary.
For KH41 its explicit CONV_ROLL_STEP=2 mode disables guidance but retains the
same base step; unset mode enables guidance. Six alternating AB/BA rounds,
five timings/process and separate DDR/HBM compare identical machine-code layout.
The helper branch and chunk policy differ at runtime. Parameter parsing remains
inside the call; this is an attribution control, not an official score or a
replacement for the accepted-root comparison. Log: `same_binary.log`.
No outcome is claimed until it completes. Root and archives unchanged.
