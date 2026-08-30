import pytest

from src.scanner import discover


def _write(path, content=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def test_discover_finds_nested_package_files(tmp_path):
    _write(tmp_path / "pkg" / "__init__.py")
    _write(tmp_path / "pkg" / "sub" / "__init__.py")
    _write(tmp_path / "pkg" / "sub" / "mod.py")

    found = discover(str(tmp_path))
    modules = {f.module for f in found}

    assert "pkg" in modules
    assert "pkg.sub" in modules
    assert "pkg.sub.mod" in modules


def test_discover_flat_directory_without_init(tmp_path):
    _write(tmp_path / "a.py")
    _write(tmp_path / "b.py")

    found = discover(str(tmp_path))
    modules = {f.module for f in found}

    assert modules == {"a", "b"}


def test_discover_respects_default_excludes(tmp_path):
    _write(tmp_path / "real.py")
    _write(tmp_path / "__pycache__" / "cached.py")
    _write(tmp_path / ".git" / "hooks.py")
    _write(tmp_path / "venv" / "lib.py")
    _write(tmp_path / "node_modules" / "thing.py")

    found = discover(str(tmp_path))
    modules = {f.module for f in found}

    assert modules == {"real"}


def test_discover_respects_custom_exclude_glob(tmp_path):
    _write(tmp_path / "keep.py")
    _write(tmp_path / "generated_stub.py")

    found = discover(str(tmp_path), exclude=["generated_*"])
    modules = {f.module for f in found}

    assert modules == {"keep"}


def test_discover_raises_for_missing_root(tmp_path):
    missing = tmp_path / "does_not_exist"
    with pytest.raises(FileNotFoundError):
        discover(str(missing))


def test_discover_ignores_non_python_files(tmp_path):
    _write(tmp_path / "notes.txt", "not python")
    _write(tmp_path / "mod.py")

    found = discover(str(tmp_path))
    modules = {f.module for f in found}

    assert modules == {"mod"}
