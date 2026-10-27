import pytest
from src.phone import normalize_us_phone

def test_country_code():
    assert normalize_us_phone("+1 (925) 555-0134") == "+19255550134"

def test_rejects_short():
    with pytest.raises(ValueError):
        normalize_us_phone("555-0134")
