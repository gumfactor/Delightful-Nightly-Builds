from src import patterns


def test_detects_aws_access_key_id():
    text = 'aws_key = "AKIAABCDEFGHIJKLMNOP"'
    matches = patterns.find_named_matches(text)
    names = [p.name for p, _v, _o in matches]
    assert "AWS Access Key ID" in names


def test_detects_github_classic_pat():
    text = 'token: ghp_' + "a" * 36
    matches = patterns.find_named_matches(text)
    names = [p.name for p, _v, _o in matches]
    assert "GitHub Personal Access Token (classic)" in names


def test_detects_pem_private_key_block():
    text = "-----BEGIN RSA PRIVATE KEY-----\nMIIB...\n-----END RSA PRIVATE KEY-----"
    matches = patterns.find_named_matches(text)
    names = [p.name for p, _v, _o in matches]
    assert "PEM Private Key Block" in names


def test_ordinary_code_has_no_named_matches():
    text = "def add(a, b):\n    return a + b\n"
    assert patterns.find_named_matches(text) == []


def test_generic_entropy_detector_flags_high_entropy_assignment():
    text = 'my_api_token = "j8Kx92mQpL0zR7vT4nH1wY6cB3sD5fA9"'
    matches = patterns.find_generic_matches(text)
    assert len(matches) == 1
    var_name, value, _offset = matches[0]
    assert "my_api_token" in var_name
    assert patterns.shannon_entropy(value) >= patterns.MIN_ENTROPY_BITS_PER_CHAR


def test_generic_entropy_detector_ignores_low_entropy_string():
    text = 'my_api_token = "aaaaaaaaaaaaaaaaaaaa"'
    assert patterns.find_generic_matches(text) == []


def test_allowlist_suppresses_known_placeholder():
    text = 'my_secret_key = "changeme"'
    assert patterns.find_generic_matches(text) == []


def test_allowlist_suppresses_repeated_char_placeholder():
    assert patterns.is_allowlisted("xxxxxxxxxxxxxxxxxxxx") is True


def test_shannon_entropy_of_empty_string_is_zero():
    assert patterns.shannon_entropy("") == 0.0


def test_shannon_entropy_higher_for_random_than_repeated():
    random_ish = "j8Kx92mQpL0zR7vT4nH1wY6cB3sD5fA9"
    repeated = "a" * len(random_ish)
    assert patterns.shannon_entropy(random_ish) > patterns.shannon_entropy(repeated)
