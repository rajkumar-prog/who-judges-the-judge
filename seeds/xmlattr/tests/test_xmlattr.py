import pytest

from jinja2 import Environment


@pytest.fixture
def env():
    return Environment()


def test_xmlattr(env):
    tmpl = env.from_string(
        "{{ {'foo': 42, 'bar': 23, 'fish': none, "
        "'spam': missing, 'blub:blub': '<?>'}|xmlattr }}"
    )
    out = tmpl.render().split()
    assert len(out) == 3
    assert 'foo="42"' in out
    assert 'bar="23"' in out
    assert 'blub:blub="&lt;?&gt;"' in out


def test_xmlattr_key_with_spaces(env):
    with pytest.raises(ValueError):
        env.from_string(
            "{{ {'src=1 onerror=alert(1)': 'my_class'}|xmlattr }}"
        ).render()
