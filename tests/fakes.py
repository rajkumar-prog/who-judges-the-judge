"""A scripted stand-in for the OpenAI client, so the loop can be tested without a key."""
import json
from types import SimpleNamespace as NS


def tool_call(name, i, **args):
    return NS(id=f"call_{i}", function=NS(name=name, arguments=json.dumps(args)))


def reply(content="", calls=None):
    msg = NS(content=content, tool_calls=calls)
    return NS(choices=[NS(message=msg)], usage=NS(prompt_tokens=100, completion_tokens=50))


class FakeClient:
    """Returns scripted replies in order; judge requests (no tools) get `verdicts` in order."""

    def __init__(self, fixer_script, verdicts):
        self.fixer_script = list(fixer_script)
        self.verdicts = list(verdicts)
        self.chat = NS(completions=NS(create=self._create))

    def _create(self, **kwargs):
        if kwargs.get("tools"):
            return self.fixer_script.pop(0)
        return reply(json.dumps(self.verdicts.pop(0)))
