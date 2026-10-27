import pytest
from src.phone import normalize_us_phone

def test_hidden():
    assert normalize_us_phone("925.555.0134") == "+19255550134"
    assert normalize_us_phone("1-312-555-0199") == "+13125550199"
    with pytest.raises(ValueError):
        normalize_us_phone("2-312-555-0199")
    with pytest.raises(ValueError):
        normalize_us_phone("")
