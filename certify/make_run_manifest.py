"""Freeze a finished campaign directory: size and SHA-256 of every file.

Usage: python3 -I make_run_manifest.py <campaign dir> <output RUN_MANIFEST.json>
The manifest is committed; the campaign directory itself is published as a release asset.
"""
import hashlib
import json
import sys
from pathlib import Path


def main(root, dest):
    root = Path(root)
    files = {}
    for path in sorted(p for p in root.rglob('*') if p.is_file()):
        data = path.read_bytes()
        files[path.relative_to(root).as_posix()] = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    for layer in range(1, 19):
        assert f'layer_{layer:02d}/complete.json' in files, f'layer {layer} is not complete'
    manifest = dict(scope=f'Every file of the campaign output directory ({root.name})', files=files)
    Path(dest).write_text(json.dumps(manifest, indent=1, sort_keys=True) + '\n')
    print(f'{len(files)} files')


if __name__ == '__main__':
    main(*sys.argv[1:3])
