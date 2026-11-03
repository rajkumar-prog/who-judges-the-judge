"""OpenAI-compatible clients for Muse Spark Open (Baseten) and hosted Muse Spark (Meta Model API)."""
import os
import sys
import time
from dataclasses import dataclass, field

PROVIDERS = {
    "baseten": {
        "base_url": "https://inference.baseten.co/v1",
        "model": "meta-models/muse-spark-open-1026",
        "key_env": "BASETEN_API_KEY",
        "label": "Baseten",
    },
    "meta": {
        "base_url": "https://api.meta.ai/v1",
        "model": os.environ.get("META_MODEL", "muse-spark-1.3"),
        "key_env": "MODEL_API_KEY",
        "label": "Meta Model API",
        # Hidden reasoning counts toward max_tokens; left to itself the model can think past the cap
        # and return nothing. "low" keeps a turn short enough to end in a tool call.
        "extra": {"reasoning_effort": os.environ.get("META_REASONING_EFFORT", "low")},
    },
}

# $ per million tokens (input, output). Rough list prices; only used for the cost column.
PRICES = {"baseten": (1.25, 4.25), "meta": (1.25, 4.25)}

# Spend across every client in this process. Set WJJ_BUDGET (dollars) to stop before going over it;
# the Meta API has no spending limit of its own.
SPENT = {"usd": 0.0}


class BudgetExceeded(RuntimeError):
    pass


def _budget() -> float | None:
    v = os.environ.get("WJJ_BUDGET")
    return float(v) if v else None


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    calls: int = 0

    def add(self, usage) -> None:
        if usage is None:
            return
        self.prompt_tokens += usage.prompt_tokens or 0
        self.completion_tokens += usage.completion_tokens or 0
        self.calls += 1

    def cost(self, provider: str) -> float:
        p_in, p_out = PRICES[provider]
        return self.prompt_tokens / 1e6 * p_in + self.completion_tokens / 1e6 * p_out


@dataclass
class LLM:
    """Thin wrapper so the rest of the code can be tested with a fake client."""
    provider: str = "baseten"
    client: object = None
    model: str = ""
    usage: Usage = field(default_factory=Usage)
    last: dict = field(default_factory=dict)  # why the latest reply ended, and its length

    def __post_init__(self):
        cfg = PROVIDERS[self.provider]
        self.model = self.model or cfg["model"]
        if self.client is None:
            from openai import OpenAI
            key = os.environ.get(cfg["key_env"])
            if not key:
                raise SystemExit(f"{cfg['key_env']} isn't set, and the {cfg['label']} model needs it. "
                                 "No key? You can still check every saved result: see 'Check it without a key' in the README.")
            self.client = OpenAI(api_key=key, base_url=cfg["base_url"])

    def chat(self, messages, tools=None, max_tokens=8000, retries=3):
        kwargs = {"model": self.model, "messages": messages, "max_tokens": max_tokens,
                  **PROVIDERS[self.provider].get("extra", {})}
        if tools:
            kwargs["tools"] = tools
        cap = _budget()
        if cap is not None and SPENT["usd"] >= cap:
            raise BudgetExceeded(f"spent ${SPENT['usd']:.2f} of the ${cap:.2f} WJJ_BUDGET, stopping")
        for attempt in range(retries):
            try:
                start = time.monotonic()
                resp = self.client.chat.completions.create(**kwargs)
                before = self.usage.cost(self.provider)
                self.usage.add(getattr(resp, "usage", None))
                SPENT["usd"] += self.usage.cost(self.provider) - before
                self._show(time.monotonic() - start, resp)
                self.last = {"finish_reason": getattr(resp.choices[0], "finish_reason", None),
                             "completion_tokens": getattr(getattr(resp, "usage", None), "completion_tokens", None)}
                return resp.choices[0].message
            except BudgetExceeded:
                raise
            except Exception:
                if attempt == retries - 1:
                    raise
                time.sleep(2 ** attempt)

    def _show(self, seconds: float, resp) -> None:
        """One line per model call on stderr, so a live run shows which model did what.
        WJJ_QUIET=1 turns it off."""
        if os.environ.get("WJJ_QUIET"):
            return
        usage = getattr(resp, "usage", None)
        out = getattr(usage, "completion_tokens", None)
        label = PROVIDERS[self.provider].get("label", self.provider)
        tokens = f" · {out} tokens" if out is not None else ""
        print(f"      [{label} · {self.model} · {seconds:.1f}s{tokens} · ${SPENT['usd']:.2f} so far]",
              file=sys.stderr, flush=True)
