"""Keep the certified engine/results frozen and the maintained reading paths usable."""
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]


class RepositoryContracts(unittest.TestCase):
    def test_frozen_engine_and_published_records_are_byte_identical(self):
        manifest = json.loads(Path(__file__).with_name('frozen_eps3e-3.json').read_text())
        for name, expected in manifest.items():
            with self.subTest(path=name):
                self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected)
        expected = {name for name in manifest if name.startswith('engine_eps3e-3/')
                    and Path(name).suffix in ('.py', '.c', '.h')}
        actual = {str(p.relative_to(ROOT)) for p in (ROOT / 'engine_eps3e-3').rglob('*')
                  if p.is_file() and p.suffix in ('.py', '.c', '.h')
                  and not any(part in ('test_diagnostics', 'build', '.venv') for part in p.parts)}
        self.assertEqual(actual, expected)

    def test_maintained_markdown_links_resolve(self):
        paths = [ROOT / name for name in ('README.md', 'CERTIFICATION.md', 'CONTROLS.md',
                 'HISTORY.md', 'REVIEW.md')]
        for folder in ('certify', 'controls', 'engine_eps3e-3', 'engine_next', 'evidence',
                       'kernel', 'model', 'proof', 'results', 'tools'):
            paths.extend((ROOT / folder).rglob('*.md'))
        for path in paths:
            if any(p in ('.venv', 'test_diagnostics') for p in path.parts):
                continue
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if re.match(r'\w+://|#|mailto:', target):
                    continue
                target = target.split('#')[0]
                if target:
                    with self.subTest(file=str(path.relative_to(ROOT)), target=target):
                        self.assertTrue((path.parent / target).exists())

    def test_readme_contains_only_requested_ai_credit(self):
        text = (ROOT / 'README.md').read_text().split('## How this was built\n', 1)[1]
        self.assertEqual(text.split('## License', 1)[0].strip(),
            'This work is done with two AI assistants, **Claude** (Anthropic) and '
            '**ChatGPT** (OpenAI), under the direction of Nicolas Breuillaud.')


if __name__ == '__main__':
    unittest.main()
