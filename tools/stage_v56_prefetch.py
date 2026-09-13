#!/usr/bin/env python3
"""Freeze the accepted source for a same-binary prefetch-distance comparison."""
from pathlib import Path
import hashlib,subprocess
root=Path('build/v56/experiments/prefetch-distance');root.mkdir(parents=True,exist_ok=True)
for name,ref,digest in [
    ('current.c','3df5c69:conv2d.c','ebf36923518cb809ae5e65001a700de30b0415956f1d0420a2dffcae45684026'),
    ('fbench.c','8b6b295:tools/fbench.c','e5e52c8d666584cc49ca6f11162be4868b240e2cc99a3c3ef0a2f8ac292c65ad')]:
    p=root/name;p.write_bytes(subprocess.check_output(['git','show',ref]))
    assert hashlib.sha256(p.read_bytes()).hexdigest()==digest
    print(digest,p)
