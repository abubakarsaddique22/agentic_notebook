"""Offline structure validation. These are NOT adversarial security pass tests."""
from pathlib import Path
import ast
import yaml
ROOT = Path(__file__).resolve().parents[1]

def test_no_promptfoo_or_other_security_frameworks():
    paths = [p for p in ROOT.rglob('*') if p.is_file() and '.venv' not in p.parts]
    assert not any('promptfoo' in p.name.lower() for p in paths)
    assert not any(p.name == 'promptfooconfig.yaml' for p in paths)
    assert not any('langchain' in str(p).lower() for p in paths)

def test_all_nemo_configs_are_yaml():
    configs = list((ROOT/'lessons').glob('*/config/config.yml'))
    assert len(configs) == 8
    for file in configs:
        obj = yaml.safe_load(file.read_text(encoding='utf-8'))
        assert obj['models'][0]['engine'] == 'openai'

def test_python_syntax():
    for file in [ROOT/'app.py', *ROOT.glob('lessons/**/actions.py')]:
        ast.parse(file.read_text(encoding='utf-8'))
