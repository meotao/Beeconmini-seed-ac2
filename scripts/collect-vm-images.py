#!/usr/bin/env python3
"""Collect only real armsr images; never treat an empty build as success."""
from pathlib import Path
import shutil,sys
src,dst=map(Path,sys.argv[1:3])
patterns=['*-armsr-armv8-generic-ext4-combined-efi.img.gz',
          '*-armsr-armv8-generic-ext4-combined-efi.qcow2',
          '*-armsr-armv8-generic-ext4-combined-efi.vmdk']
images=[]
for pattern in patterns:
    matches=list(src.glob(pattern))
    if len(matches)!=1 or matches[0].stat().st_size==0:
        raise SystemExit(f'Missing or ambiguous VM image: {pattern}: {matches}')
    images.extend(matches)
dst.mkdir(parents=True,exist_ok=True)
for p in images:
    shutil.copy2(p,dst/p.name)
for pattern in ('*.manifest','config.buildinfo','feeds.buildinfo','version.buildinfo','*-kernel.bin'):
    for p in src.glob(pattern):
        if p.is_file(): shutil.copy2(p,dst/p.name)
print('Collected:',*[p.name for p in images],sep='\n')
