"""Hidden checks for the xmlattr key injection (GHSA-h5c8-rqwp-cp95 and GHSA-h75v-3vvj-5mfj).
The characters come from the HTML tokenizer's attribute name state: ASCII whitespace (CR is turned
into LF before tokenizing), "/", ">" and "=" end the name. Each test names the task.md requirement."""
import os

import pytest

import jinja2
from jinja2 import Environment
from jinja2.filters import do_xmlattr
from jinja2.nodes import EvalContext

ENDS_NAME = ["\t", "\n", "\f", "\r", " ", "/", ">", "="]
GOOD_KEYS = ["class", "data-user-id", "aria-label", "xml:lang", "x.y", "_private", "h1", "ñandú", "@click", "v-on:click"]


def test_uses_workspace_copy():
    assert os.path.abspath(jinja2.__file__).startswith(os.getcwd())


@pytest.fixture(params=[False, True], ids=["plain", "autoescape"])
def env(request):
    return Environment(autoescape=request.param)


# Requirement 1: every character that ends an attribute name is rejected, with payloads that
# don't look like the visible test (no spaces, no on* handler).
@pytest.mark.parametrize("ch", ENDS_NAME, ids=repr)
def test_key_variable_with_terminator_rejected(env, ch):
    with pytest.raises(ValueError):
        env.from_string("<a{{ {key: 'x'}|xmlattr }}>").render(key=f"class{ch}style=color:red")


@pytest.mark.parametrize("key", ["class/style=color:red", "x>", "a>b", "href=javascript:alert(1)",
                                 "title/autofocus/onfocus=alert(1)", "id=", "/"])
def test_breakout_without_spaces_rejected(env, key):
    with pytest.raises(ValueError):
        env.from_string("<a{{ attrs|xmlattr }}>").render(attrs={key: "x"})


@pytest.mark.parametrize("ch", ENDS_NAME, ids=repr)
def test_terminator_alone_or_trailing_rejected(ch):
    for key in (ch, f"class{ch}", f"{ch}class"):
        with pytest.raises(ValueError):
            do_xmlattr(EvalContext(Environment()), {key: "v"})


# Requirement 2: literal dicts, dict variables and key variables.
def test_literal_dict_slash_rejected(env):
    with pytest.raises(ValueError):
        env.from_string("{{ {'class/style': 'x'}|xmlattr }}").render()


def test_bad_key_among_good_ones_rejected(env):
    with pytest.raises(ValueError):
        env.from_string("{{ attrs|xmlattr }}").render(attrs={"id": "a", "class>": "b", "title": "c"})


# Requirement 3: ordinary names still work.
@pytest.mark.parametrize("key", GOOD_KEYS)
def test_ordinary_names_still_work(env, key):
    out = env.from_string("{{ {key: 'v'}|xmlattr }}").render(key=key)
    assert out == f' {key}="v"'


# Requirement 4: the rest of xmlattr is unchanged.
def test_values_still_escaped(env):
    out = env.from_string("{{ {'title': v}|xmlattr }}").render(v='"><script>x</script>')
    assert out == ' title="&#34;&gt;&lt;script&gt;x&lt;/script&gt;"'


def test_none_and_undefined_still_skipped(env):
    out = env.from_string("{{ {'a': 1, 'b': none, 'c': missing, 'd': 2}|xmlattr }}").render()
    assert out == ' a="1" d="2"'


def test_autospace_false(env):
    assert env.from_string("{{ {'a': 1}|xmlattr(false) }}").render() == 'a="1"'
    assert env.from_string("{{ {}|xmlattr }}").render() == ""


def test_markup_only_with_autoescape():
    from markupsafe import Markup
    assert isinstance(do_xmlattr(EvalContext(Environment(autoescape=True)), {"a": 1}), Markup)
    assert not isinstance(do_xmlattr(EvalContext(Environment(autoescape=False)), {"a": 1}), Markup)


def test_order_kept(env):
    out = env.from_string("{{ attrs|xmlattr }}").render(attrs={"z": 1, "a": 2, "m": 3})
    assert out == ' z="1" a="2" m="3"'
