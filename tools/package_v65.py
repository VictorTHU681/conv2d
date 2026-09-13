#!/usr/bin/env python3
"""Reproduce v65 archives and verify the server-qualified program members."""
from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent
STAGE = ROOT / 'build/v65/release'
OUT = ROOT / 'results/v65'
OPERATORS = {
    'conv.zip': 'f88b3f90295fd5ad5a749016343b266535857b53d2588801f65e18e6c7f2d499',
    'conv_nf3.zip': 'cb4ffaa47f9c0eecb8904c416fb61033ec12c83864cfcdaa70fe43e44ba58175',
    'conv_diag.zip': 'c2b90093e2d39b93358ca9484e0dd54bd3c429c2fffc045db401b74a48515b5f',
}
FILES = {
    'bench_conv.c': '2548861ae7e29826e454b4c0b098d682f7f04996222e664cd1ea9bc92dd2e927',
    'run.sh': 'f534c477d6b6e4f552860c374c2e8c138d027b4e9adc1bceade4b4745db61474',
    'run_diag.sh': 'cc88f911feea05a406124206c21c4601fbc6722f07aa178eb66d0adf62982386',
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    for name, expected in {**FILES, 'conv2d.c': OPERATORS['conv.zip']}.items():
        require(digest((ROOT / name).read_bytes()) == expected, f'Changed release input: {name}')
    (STAGE / 'tools').mkdir(parents=True, exist_ok=True)
    (STAGE / 'submissions').mkdir(exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (ROOT / 'submissions').mkdir(exist_ok=True)
    for name in ['conv2d.c', *FILES, 'tools/mkdiag.py', 'tools/package_v56.py']:
        shutil.copyfile(ROOT / name, STAGE / name)
    readme = (ROOT / 'docs/v65-package.md').read_bytes()
    (STAGE / 'README.md').write_bytes(readme)
    subprocess.run([sys.executable, str(STAGE / 'tools/package_v56.py')], check=True)
    manifest = []
    audit = ['Program hashes pinned to the archives qualified by job 1593101.',
             'Only README differs from those qualified archives.']
    for name, operator in OPERATORS.items():
        archive = STAGE / 'submissions' / name
        script = 'run_diag.sh' if name == 'conv_diag.zip' else 'run.sh'
        expected = {'conv/conv2d.c': operator, 'conv/bench_conv.c': FILES['bench_conv.c'],
                    'conv/run.sh': FILES[script], 'conv/README.md': digest(readme)}
        with zipfile.ZipFile(archive) as z:
            require(len(z.namelist()) == 4 and set(z.namelist()) == set(expected), f'Members: {name}')
            for member, sha in expected.items():
                require(digest(z.read(member)) == sha, f'Member changed: {name}/{member}')
                mode = 0o100755 if member == 'conv/run.sh' else 0o100644
                require(z.getinfo(member).external_attr >> 16 == mode, f'Mode: {name}/{member}')
                audit.append(f'{name} {member} {sha} PASS')
        manifest.append(f'{digest(archive.read_bytes())}  submissions/{name}\n')
    # Publish only after all three archives have passed member validation.
    for name in OPERATORS:
        shutil.copyfile(STAGE / 'submissions' / name, ROOT / 'submissions' / name)
    (OUT / 'archives.sha256').write_text(''.join(manifest))
    (OUT / 'member_audit.txt').write_text('\n'.join(audit) + '\n')
    print(''.join(manifest), end='')


if __name__ == '__main__':
    main()
