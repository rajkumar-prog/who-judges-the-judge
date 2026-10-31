from src.text import slugify

def test_hidden():
    assert slugify("  Multiple   spaces here ") == "multiple-spaces-here"
    assert slugify("C++ & Rust: a tale") == "c-rust-a-tale"
    assert slugify("already-a-slug") == "already-a-slug"
    assert slugify("---") == ""


def test_underscore_is_not_alphanumeric():
    assert slugify("snake_case title") == "snake-case-title"
