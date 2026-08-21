from src import redact


def test_mask_value_keeps_only_prefix_and_suffix():
    raw = "AKIAABCDEFGHIJKLMNOP"
    masked = redact.mask_value(raw)
    assert masked.startswith(raw[:4])
    assert masked.endswith(raw[-4:])
    assert redact.MASK_CHAR in masked
    assert raw not in masked  # the full raw value never appears in the masked preview


def test_mask_value_fully_masks_short_values():
    raw = "short12"
    masked = redact.mask_value(raw)
    assert masked == redact.MASK_CHAR * len(raw)
    assert "short" not in masked


def test_hash_value_is_deterministic_and_64_hex_chars():
    raw = "some-secret-value"
    h1 = redact.hash_value(raw)
    h2 = redact.hash_value(raw)
    assert h1 == h2
    assert len(h1) == 64
    assert all(c in "0123456789abcdef" for c in h1)


def test_hash_value_differs_for_different_inputs():
    assert redact.hash_value("secret-a") != redact.hash_value("secret-b")


def test_masked_context_never_contains_raw_value():
    raw = "sk-ant-supersecretvalue1234567890"
    ctx = redact.masked_context("api_key = '", raw, "'  # loaded at startup")
    assert raw not in ctx
    assert "[REDACTED]" in ctx
    assert ctx.startswith("api_key = '")
    assert ctx.endswith("'  # loaded at startup")
