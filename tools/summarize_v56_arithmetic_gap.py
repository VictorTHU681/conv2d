#!/usr/bin/env python3
"""Audit same-job calibration, source work counts, and uninstrumented wall time."""
from collections import defaultdict
from pathlib import Path
from statistics import mean, median
import re
import sys

s = Path(sys.argv[1]).read_text()
assert 'ARITHMETIC_GAP_DONE' in s and 'FAIL' not in s
for line in Path('results/v56/experiments/arithmetic-gap/sources.sha256').read_text().splitlines():
    digest, path = line.split()
    assert re.search(r'^' + digest + r'\s+' + re.escape(path) + r'$', s, re.M)
for binary in ['plain', 'profile', 'probe']:
    assert re.search(r'^[0-9a-f]{64}\s+build/v56/experiments/arithmetic-gap/' + binary + r'$', s, re.M)
m = re.search(r'^PLACEMENT cpu_node=\d+ hbm_node=(-?\d+)$', s, re.M)
assert m
memories = ['DDR'] if int(m[1]) < 0 else ['DDR', 'HBM']
shapes = {39: (4096, 6144, 39, 39), 41: (6144, 4096, 41, 41),
          55: (4256, 6390, 55, 55), 81: (6390, 4256, 81, 81)}
buckets = {39: [0, 3], 41: [0, 3], 55: [0, 1, 3], 81: [0, 2]}
variants = ['mix' + str(n) for n in (0, 2, 4, 6, 8, 10, 12, 16, 18)]
variants += ['vec' + str(n) for n in (2, 4, 8, 16, 18)]
events = []
probe = {}
timers = {}
probe_orders = defaultdict(list)
hosts, threads, costs, tables, wall = {}, {}, {}, {}, {}
counts = defaultdict(list)
key = calibration = None
for line in s.splitlines():
    m = re.match(r'ARITHMETIC_CALIBRATION round=(\d+) side=(before|after) ', line)
    if m:
        assert key is None
        calibration = int(m[1]), m[2]
        events.append(('calibration',) + calibration)
    m = re.match(r'MIXED_TIMER_HZ (\d+) threads=(\d+) outer_iters=(\d+) steps_per_iter=(\d+)$', line)
    if m:
        assert calibration is not None and calibration not in timers
        assert tuple(map(int, m.groups()[1:])) == (38, 1000000, 4)
        timers[calibration] = int(m[1])
        assert timers[calibration] > 0
    m = re.match(r'MIXED_THROUGHPUT round=(\d+) variant=(\w+) threads=(\d+) ns_per_step_min=([\d.]+) mean=([\d.]+) max=([\d.]+)$', line)
    if m:
        assert calibration in timers and int(m[3]) == 38
        k = calibration + (int(m[1]), m[2])
        assert k not in probe
        probe[k] = tuple(map(float, m.groups()[3:]))
        assert 0 < probe[k][0] <= probe[k][1] <= probe[k][2]
        probe_orders[calibration + (int(m[1]),)].append(m[2])
    m = re.match(r'ARITHMETIC_CONV memory=(\w+) round=(\d+) variant=(plain|profile) shape=(\d+) (\d+) (\d+) (\d+)$', line)
    if m:
        assert key is None
        kh = int(m[6])
        assert tuple(map(int, m.groups()[3:])) == shapes[kh]
        key = m[1], int(m[2]), m[3], kh
        calibration = None
        events.append(('conv',) + key)
    for prefix, dest in [('K5_PHASE ', hosts), ('K5_THREAD ', threads),
                         ('K5_COST ', costs), ('TABLE_WORK ', tables)]:
        if line.startswith(prefix):
            assert key is not None and key[2] == 'profile'
            fields = dict(re.findall(r'(\w+)=([\d.]+)', line))
            call = int(fields.pop('call'))
            k = (key[0], key[1], key[3], call)
            if prefix == 'K5_THREAD ':
                k += (int(fields.pop('tid')),)
            if prefix == 'K5_COST ':
                k += (int(fields.pop('bucket')),)
            assert k not in dest
            dest[k] = {n: float(v) for n, v in fields.items()}
    m = re.search(r' run(\d+)\s+[\d.]+ ms\s+[\d.]+ GFLOPS PASS$', line)
    if m:
        assert key is not None
        counts[key].append(int(m[1]))
    m = re.search(r'\| avg\s+([\d.]+) ms\s+([\d.]+) GFLOPS\s+PASS$', line)
    if m:
        assert key is not None and key not in wall and counts[key] == list(range(5))
        wall[key] = float(m[1]) * 1000
        key = None
assert key is None
expected = []
for r in range(4):
    expected.append(('calibration', r, 'before'))
    order = ['plain', 'profile'] if r % 2 == 0 else ['profile', 'plain']
    for memory in memories:
        for kh in list(shapes)[r:] + list(shapes)[:r]:
            for v in order:
                expected.append(('conv', memory, r, v, kh))
    expected.append(('calibration', r, 'after'))
assert events == expected
calibrations = {(r, side) for r in range(4) for side in ['before', 'after']}
assert set(timers) == calibrations and len(set(timers.values())) == 1
assert set(probe) == {c + (r, v) for c in calibrations for r in range(3) for v in variants}
for c in calibrations:
    for r in range(3):
        assert probe_orders[c + (r,)] == (variants if r % 2 == 0 else variants[::-1])
blocks = {(m, r, v, kh) for m in memories for r in range(4)
          for v in ['plain', 'profile'] for kh in shapes}
assert set(wall) == set(counts) == blocks
calls = {(m, r, kh, c) for m in memories for r in range(4) for kh in shapes for c in range(1, 8)}
assert set(hosts) == set(tables) == calls
assert set(threads) == {k + (t,) for k in calls for t in range(38)}
assert set(costs) == {k + (b,) for k in calls for b in buckets[k[2]]}
work = {}
for kh in shapes:
    work_rows, storage = set(), set()
    for k in calls:
        if k[2] != kh:
            continue
        ts = [threads[k + (t,)] for t in range(38)]
        cs = [costs[k + (b,)] for b in buckets[kh]]
        work_rows.add(tuple(c['tile_steps'] for c in cs))
        storage.add(tuple(sorted(tables[k].items())))
        assert sum(t['main_steps'] + t['tail_steps'] for t in ts) == sum(c['tile_steps'] for c in cs)
        assert abs(mean(t['main_us'] for t in ts) - costs[k + (0,)]['kernel_mean_us']) < 0.002
        assert abs(mean(t['tail_us'] for t in ts) - sum(costs[k + (b,)]['kernel_mean_us'] for b in buckets[kh] if b != 0)) < 0.004
        assert all(t['main_us'] + t['tail_us'] <= t['duration_us'] + 0.003 for t in ts)
    assert len(work_rows) == len(storage) == 1
    work[kh] = dict(zip(buckets[kh], work_rows.pop()))

def calibration_ns(r, side, v):
    return median(probe[r, side, j, v][1] for j in range(3))

def ref_us(r, kh, bucket=None, variant='mix0'):
    ns = mean(calibration_ns(r, side, variant) for side in ['before', 'after'])
    steps = sum(work[kh].values()) if bucket is None else work[kh][bucket]
    return steps / 4 * ns / 38 / 1000

def phase_metric(memory, r, kh, name):
    return median(hosts[memory, r, kh, c][name] for c in range(3, 8))

def kernel_us(memory, r, kh, bucket):
    return median(costs[memory, r, kh, c, bucket]['kernel_mean_us'] for c in range(3, 8))

print(f'{len(probe)} calibration rows; {len(wall)} convolution processes, {len(threads)} worker records, {sum(map(len, counts.values()))} timed hashes validate.')
print('Accepted ebf36923 source; one node/job. Four rotating shape orders, alternating plain/profile order. Calibration brackets every round; each bracket has three alternating probe orders. No assumed core frequency. Work totals are source-counted FMOPA tile steps, including chunk warmup and padded execution; they are not hardware instruction-counter readings.')
print('\nCalibration: median of three per-thread means, ns per four-FMOPA step (mix8 additionally executes eight indexed FMLAs). All probe variants and outliers retained in the log.')
print('\n| Round | mix0 before ns | mix0 after ns | Drift | mix8 before ns | mix8 after ns | Drift |')
print('| --- | ---: | ---: | ---: | ---: | ---: | ---: |')
for r in range(4):
    vals = []
    for v in ['mix0', 'mix8']:
        a, b = [calibration_ns(r, side, v) for side in ['before', 'after']]
        vals.extend([f'{a:.6f}', f'{b:.6f}', f'{100*(b/a-1):+.3f}%'])
    print(f'| {r} | ' + ' | '.join(vals) + ' |')
for v in variants:
    xs = [probe[k][1] for k in probe if k[-1] == v]
    print(f'{v}: all 24 means median={median(xs):.6f} range={min(xs):.6f}..{max(xs):.6f} ns/step')
print('\nRegister-only reference: sum(tile_steps)/4 * bracket_mean(ns_per_step) / 38 / 1000 us. This projects perfectly balanced independent arithmetic; it is neither a rigorous architectural lower bound nor guaranteed recoverable headroom. Real kernels also perform loads, copies, ZA transfers, output events and scheduling. mix8 is sensitivity, not an exact instruction-mix model for every bucket.')
print('\n| Memory | KH | Plain wall us | Profile wall us | Profile wall overhead | mix0 reference us | mix8 reference us | Plain wall / mix0 ref | Worker end spread us |')
print('| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
for memory in memories:
    for kh in shapes:
        plain = median(wall[memory, r, 'plain', kh] for r in range(4))
        profile = median(wall[memory, r, 'profile', kh] for r in range(4))
        refs = [median(ref_us(r, kh, variant=v) for r in range(4)) for v in ['mix0', 'mix8']]
        gap = []
        for r in range(4):
            calls_gap = []
            for c in range(3, 8):
                ends = [threads[memory, r, kh, c, t]['end_us'] for t in range(38)]
                calls_gap.append(max(ends) - mean(ends))
            gap.append(median(calls_gap))
        print(f'| {memory} | {kh} | {plain:.3f} | {profile:.3f} | {100*(profile/plain-1):+.2f}% | {refs[0]:.3f} | {refs[1]:.3f} | {plain/refs[0]:.3f} | {median(gap):.3f} |')
print('\nRegion times: median of four process medians, timed calls 3–7. Per-worker means, not serialized stages. Timers include argument setup and ZA restoration; profile wall also includes diagnostic reporting. Reference differences cannot identify a particular hardware stall or be advertised as speedups.')
print('\n| Memory | KH | Bucket | Tile steps | Region us/thread | mix0 reference us/thread | Difference us | Region / reference |')
print('| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |')
names = {0: 'pair', 1: 'single16', 2: 'K8/K9', 3: 'K4/K5'}
for memory in memories:
    for kh in shapes:
        for b in buckets[kh]:
            region = median(kernel_us(memory, r, kh, b) for r in range(4))
            ref = median(ref_us(r, kh, b) for r in range(4))
            print(f'| {memory} | {kh} | {names[b]} | {int(work[kh][b])} | {region:.3f} | {ref:.3f} | {region-ref:.3f} | {region/ref:.3f} |')
print('\n| Memory | KH | Prepare us | Dispatch us | Workers us | Mean pack us/thread |')
print('| --- | ---: | ---: | ---: | ---: | ---: |')
for memory in memories:
    for kh in shapes:
        values = [median(phase_metric(memory, r, kh, n) for r in range(4))
                  for n in ['prepare_us', 'dispatch_us', 'workers_us', 'pack_mean_us']]
        print(f'| {memory} | {kh} | ' + ' | '.join(f'{v:.3f}' for v in values) + ' |')
