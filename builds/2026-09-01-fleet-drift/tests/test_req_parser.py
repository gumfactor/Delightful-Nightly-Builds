from src.req_parser import parse_requirements


def test_parses_exact_pin():
    entries = parse_requirements("requests==2.31.0\n")
    assert entries == [{"name": "requests", "pinned_version": "2.31.0", "pin_kind": "exact"}]


def test_skips_comments_and_blank_lines():
    text = "\n# a comment\nrequests==2.31.0\n\n"
    entries = parse_requirements(text)
    assert len(entries) == 1
    assert entries[0]["name"] == "requests"


def test_strips_inline_comment():
    entries = parse_requirements("requests==2.31.0  # pinned for httpx compat\n")
    assert entries == [{"name": "requests", "pinned_version": "2.31.0", "pin_kind": "exact"}]


def test_handles_extras():
    entries = parse_requirements("uvicorn[standard]==0.30.1\n")
    assert entries == [{"name": "uvicorn", "pinned_version": "0.30.1", "pin_kind": "exact"}]


def test_strips_environment_marker():
    entries = parse_requirements('pywin32==306 ; platform_system == "Windows"\n')
    assert entries == [{"name": "pywin32", "pinned_version": "306", "pin_kind": "exact"}]


def test_skips_dash_r_include_lines():
    entries = parse_requirements("-r base.txt\nrequests==2.31.0\n")
    assert len(entries) == 1 and entries[0]["name"] == "requests"


def test_skips_editable_install_lines():
    entries = parse_requirements("-e .\nrequests==2.31.0\n")
    assert len(entries) == 1 and entries[0]["name"] == "requests"


def test_skips_vcs_and_url_lines():
    text = "git+https://github.com/org/repo.git@main#egg=repo\nhttps://example.com/pkg.whl\nrequests==2.31.0\n"
    entries = parse_requirements(text)
    assert len(entries) == 1 and entries[0]["name"] == "requests"


def test_bare_name_recorded_as_unparseable_not_dropped():
    entries = parse_requirements("numpy\n")
    assert entries == [{"name": "numpy", "pinned_version": None, "pin_kind": "unparseable"}]


def test_range_operator_recorded_as_range():
    entries = parse_requirements("pandas>=2.0.0\n")
    assert entries == [{"name": "pandas", "pinned_version": "2.0.0", "pin_kind": "range"}]


def test_empty_file_returns_empty_list():
    assert parse_requirements("") == []
