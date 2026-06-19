"""Tests for src/parser.py — all pure string-input, no network or filesystem."""
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import pytest
from src.parser import parse_requirements_txt, parse_setup_cfg, parse_pipfile


# ---------------------------------------------------------------------------
# parse_requirements_txt
# ---------------------------------------------------------------------------

class TestParseRequirementsTxt:
    def test_simple_pinned_package(self):
        reqs = parse_requirements_txt("requests==2.28.0\n")
        assert len(reqs) == 1
        assert reqs[0].name == "requests"
        assert reqs[0].pinned_version == "2.28.0"

    def test_package_with_gte_specifier_not_pinned(self):
        reqs = parse_requirements_txt("requests>=2.28.0\n")
        assert len(reqs) == 1
        assert reqs[0].name == "requests"
        assert reqs[0].pinned_version is None
        assert reqs[0].specifier == ">=2.28.0"

    def test_comment_only_line_is_skipped(self):
        reqs = parse_requirements_txt("# this is a comment\n")
        assert reqs == []

    def test_blank_lines_are_skipped(self):
        reqs = parse_requirements_txt("\n\n   \n")
        assert reqs == []

    def test_inline_comment_is_stripped(self):
        reqs = parse_requirements_txt("requests==2.28.0  # HTTP library\n")
        assert len(reqs) == 1
        assert reqs[0].pinned_version == "2.28.0"

    def test_package_name_normalised_to_lowercase(self):
        reqs = parse_requirements_txt("Requests==2.28.0\n")
        assert reqs[0].name == "requests"

    def test_underscores_normalised_to_hyphens(self):
        reqs = parse_requirements_txt("my_package==1.0.0\n")
        assert reqs[0].name == "my-package"

    def test_package_with_extras_parsed(self):
        reqs = parse_requirements_txt("requests[security]==2.28.0\n")
        assert len(reqs) == 1
        assert reqs[0].name == "requests"
        assert reqs[0].pinned_version == "2.28.0"

    def test_environment_marker_stripped(self):
        reqs = parse_requirements_txt('requests==2.28.0; python_version >= "3.8"\n')
        assert len(reqs) == 1
        assert reqs[0].pinned_version == "2.28.0"

    def test_git_url_entry_is_skipped(self):
        reqs = parse_requirements_txt("git+https://github.com/example/repo.git\n")
        assert reqs == []

    def test_multiple_packages_parsed(self):
        text = "requests==2.28.0\nflask==2.3.0\nnumpy==1.24.0\n"
        reqs = parse_requirements_txt(text)
        assert len(reqs) == 3
        names = {r.name for r in reqs}
        assert names == {"requests", "flask", "numpy"}

    def test_unpinned_package_no_specifier(self):
        reqs = parse_requirements_txt("requests\n")
        assert len(reqs) == 1
        assert reqs[0].pinned_version is None
        assert reqs[0].specifier is None

    def test_source_file_is_recorded(self):
        reqs = parse_requirements_txt("requests==2.28.0\n", source_file="my-reqs.txt")
        assert reqs[0].source_file == "my-reqs.txt"

    def test_empty_input_returns_empty_list(self):
        reqs = parse_requirements_txt("")
        assert reqs == []


# ---------------------------------------------------------------------------
# parse_setup_cfg
# ---------------------------------------------------------------------------

class TestParseSetupCfg:
    def test_basic_install_requires(self):
        text = "[options]\ninstall_requires =\n    requests>=2.28.0\n    flask==2.3.0\n"
        reqs = parse_setup_cfg(text)
        assert len(reqs) == 2
        names = {r.name for r in reqs}
        assert names == {"requests", "flask"}

    def test_missing_options_section_returns_empty(self):
        text = "[metadata]\nname = mypackage\n"
        reqs = parse_setup_cfg(text)
        assert reqs == []

    def test_empty_install_requires_returns_empty(self):
        text = "[options]\ninstall_requires =\n"
        reqs = parse_setup_cfg(text)
        assert reqs == []


# ---------------------------------------------------------------------------
# parse_pipfile
# ---------------------------------------------------------------------------

class TestParsePipfile:
    def test_pinned_package(self):
        text = '[packages]\nrequests = "==2.28.0"\n'
        reqs = parse_pipfile(text)
        assert len(reqs) == 1
        assert reqs[0].name == "requests"
        assert reqs[0].pinned_version == "2.28.0"

    def test_wildcard_package_is_unpinned(self):
        text = '[packages]\nrequests = "*"\n'
        reqs = parse_pipfile(text)
        assert len(reqs) == 1
        assert reqs[0].pinned_version is None

    def test_dev_packages_section_parsed(self):
        text = '[dev-packages]\npytest = "==7.4.0"\n'
        reqs = parse_pipfile(text)
        assert len(reqs) == 1
        assert reqs[0].name == "pytest"

    def test_package_not_in_packages_section_skipped(self):
        text = "[source]\nurl = https://pypi.org/simple\n"
        reqs = parse_pipfile(text)
        assert reqs == []

    def test_empty_pipfile_returns_empty(self):
        reqs = parse_pipfile("")
        assert reqs == []
