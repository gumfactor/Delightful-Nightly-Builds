import sys

from src.ast_parser import parse_file
from src.scanner import discover

STDLIB = set(getattr(sys, "stdlib_module_names", ()))


def _setup(tmp_path, files: dict[str, str]):
    for rel_path, content in files.items():
        full = tmp_path / rel_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content)
    source_files = discover(str(tmp_path))
    known = {f.module for f in source_files}
    by_module = {f.module: f for f in source_files}
    return by_module, known


def test_absolute_first_party_import(tmp_path):
    by_module, known = _setup(
        tmp_path,
        {
            "pkg/__init__.py": "",
            "pkg/sub.py": "",
            "app.py": "import pkg.sub\n",
        },
    )
    refs, warning = parse_file(by_module["app"], known, STDLIB)
    assert warning is None
    assert any(r.kind == "first_party" and r.target == "pkg.sub" for r in refs)


def test_stdlib_import_classified_correctly(tmp_path):
    by_module, known = _setup(tmp_path, {"app.py": "import os\nimport json\n"})
    refs, _ = parse_file(by_module["app"], known, STDLIB)
    kinds = {r.target: r.kind for r in refs}
    assert kinds["os"] == "stdlib"
    assert kinds["json"] == "stdlib"


def test_external_third_party_import(tmp_path):
    by_module, known = _setup(tmp_path, {"app.py": "import totally_not_a_real_package\n"})
    refs, _ = parse_file(by_module["app"], known, STDLIB)
    assert refs[0].kind == "external"


def test_import_with_as_alias_still_classified(tmp_path):
    by_module, known = _setup(
        tmp_path,
        {"pkg/__init__.py": "", "pkg/sub.py": "", "app.py": "import pkg.sub as ps\n"},
    )
    refs, _ = parse_file(by_module["app"], known, STDLIB)
    assert refs[0].kind == "first_party"
    assert refs[0].target == "pkg.sub"


def test_from_import_submodule_progressive_prefix(tmp_path):
    by_module, known = _setup(
        tmp_path,
        {
            "pkg/__init__.py": "",
            "pkg/sub.py": "",
            "app.py": "from pkg import sub\n",
        },
    )
    refs, _ = parse_file(by_module["app"], known, STDLIB)
    assert refs[0].kind == "first_party"
    assert refs[0].target == "pkg.sub"


def test_from_import_attribute_falls_back_to_containing_module(tmp_path):
    by_module, known = _setup(
        tmp_path,
        {
            "pkg/__init__.py": "",
            "pkg/sub.py": "SOME_CONSTANT = 1\n",
            "app.py": "from pkg.sub import SOME_CONSTANT\n",
        },
    )
    refs, _ = parse_file(by_module["app"], known, STDLIB)
    # SOME_CONSTANT is not itself a module, so it should resolve to pkg.sub
    assert refs[0].kind == "first_party"
    assert refs[0].target == "pkg.sub"


def test_multi_name_from_import_produces_multiple_refs(tmp_path):
    by_module, known = _setup(
        tmp_path,
        {
            "pkg/__init__.py": "",
            "pkg/a.py": "",
            "pkg/b.py": "",
            "app.py": "from pkg import a, b\n",
        },
    )
    refs, _ = parse_file(by_module["app"], known, STDLIB)
    targets = {r.target for r in refs}
    assert targets == {"pkg.a", "pkg.b"}


def test_relative_import_level_one_from_sibling(tmp_path):
    by_module, known = _setup(
        tmp_path,
        {
            "pkg/__init__.py": "",
            "pkg/a.py": "from . import b\n",
            "pkg/b.py": "",
        },
    )
    refs, _ = parse_file(by_module["pkg.a"], known, STDLIB)
    assert refs[0].kind == "first_party"
    assert refs[0].target == "pkg.b"


def test_relative_import_with_explicit_submodule(tmp_path):
    by_module, known = _setup(
        tmp_path,
        {
            "pkg/__init__.py": "",
            "pkg/sub/__init__.py": "",
            "pkg/sub/mod.py": "",
            "pkg/a.py": "from .sub import mod\n",
        },
    )
    refs, _ = parse_file(by_module["pkg.a"], known, STDLIB)
    assert refs[0].target == "pkg.sub.mod"


def test_relative_import_level_two_goes_up_a_package(tmp_path):
    by_module, known = _setup(
        tmp_path,
        {
            "pkg/__init__.py": "",
            "pkg/sub/__init__.py": "",
            "pkg/sub/deep.py": "from .. import top\n",
            "pkg/top.py": "",
        },
    )
    refs, _ = parse_file(by_module["pkg.sub.deep"], known, STDLIB)
    assert refs[0].target == "pkg.top"


def test_star_import_resolves_to_base_module(tmp_path):
    by_module, known = _setup(
        tmp_path,
        {"pkg/__init__.py": "", "app.py": "from pkg import *\n"},
    )
    refs, _ = parse_file(by_module["app"], known, STDLIB)
    assert refs[0].kind == "first_party"
    assert refs[0].target == "pkg"


def test_syntax_error_file_returns_warning_not_crash(tmp_path):
    by_module, known = _setup(tmp_path, {"broken.py": "def oops(:\n"})
    refs, warning = parse_file(by_module["broken"], known, STDLIB)
    assert refs == []
    assert warning is not None
    assert "syntax error" in warning.lower()
