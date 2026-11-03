from pathlib import Path
import ast
import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_original_rag_restored():
    assert (ROOT / "agent/runtime.py").exists()
    assert (ROOT / "rag/store.py").exists()
    assert (ROOT / "ingest.py").exists()
    assert "create_agent" in (ROOT / "agent/runtime.py").read_text(encoding="utf-8")
    assert "Chroma" in (ROOT / "rag/store.py").read_text(encoding="utf-8")


def test_single_config_without_promptfoo():
    assert not (ROOT / "security").exists()
    assert len(list(ROOT.rglob("promptfooconfig.yaml"))) == 0
    assert len(list(ROOT.rglob("config.yml"))) == 1
    assert "RunnableRails" in (ROOT / "app.py").read_text(encoding="utf-8")
    assert yaml.safe_load((ROOT / "config/config.yml").read_text(encoding="utf-8"))["rails"]


def test_python_files_parse():
    for path in ROOT.rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_untrusted_document_screen():
    source = (ROOT / "config/actions.py").read_text(encoding="utf-8")
    assert "inspect_tool_documents" in source
    assert "ignore previous instructions" in source
