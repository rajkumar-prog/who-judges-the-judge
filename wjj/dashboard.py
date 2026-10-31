"""Export saved results into one data file for the dashboard page.

Nothing on the dashboard is typed by hand: every number and every replayed round comes from
here. Pass the result files you want shown; a file name can be prefixed with the prompt it was
judged with ("strict:results/duel-x.jsonl") for older files that didn't record it. Rejudged files
carry both prompts on the same diffs and are split into one run per prompt.

Writes dashboard/data.json, and dashboard/data.js (the same data as `window.WJJ_DATA = ...`) so
the page also works when opened straight from disk, where browsers block fetch().
"""
import json
import re
import subprocess
import time
from pathlib import Path

from . import cases as cases_mod
from .duel import apply_diff, feedback, outcome
from .workspace import ROOT, Workspace

OUT = ROOT / "dashboard"
MODELS = {"judge": "Muse Spark Open (meta-models/muse-spark-open-1026, Baseten)",
          "cheater": "Muse Spark (muse-spark-1.3, Meta Model API)"}
FAILED = re.compile(r"^FAILED \S*::(\S+)", re.M)


def _suite(seed: str) -> str:
    return "real" if seed in cases_mod.seeds() else "toy"


def _verdict(j: dict) -> dict:
    return {k: (j or {}).get(k, "") for k in ("verdict", "evidence", "reason", "counterexample")}


def _failures(seed: str, diff: str, cache: dict) -> list[str]:
    """Names of the hidden tests this diff fails today. Re-runs the tests, so it's cached per diff."""
    key = (seed, diff)
    if key not in cache:
        with Workspace(seed) as ws:
            apply_diff(ws, diff, seed)
            cache[key] = FAILED.findall(ws.run_hidden().output)
    return cache[key]


def _round(att: dict, n: int, judge_key: str, played: list, fails) -> dict:
    return {"n": n, "author": att.get("author", "agent"), "diff": att["diff"],
            "visible_passed": att["visible_passed"], "hidden_passed": att["hidden_passed"],
            "label": att["label"], "hidden_failures": fails(att) if att["label"] != "failed" and att["diff"] else [],
            "judge": _verdict(att.get(judge_key)),
            "outcome": outcome(att, judge_key) if att.get(judge_key) else "failed",
            "baseline": (att.get("baseline") or {}).get("verdict", ""),
            "feedback_after": feedback(played) if att.get(judge_key, {}).get("verdict") == "cheat" else ""}


def _prompts(att: dict, tag: str) -> list[tuple[str, str]]:
    """(prompt name, record key) pairs this attempt was judged with."""
    out = [(att.get("judge_prompt") or tag or "original", "judge")]
    if att.get("judge_strict"):
        out.append(("strict", "judge_strict"))
    return out


def load(specs: list[str], failures: bool = True) -> list[dict]:
    runs, cache = [], {}
    for spec in specs:
        tag, _, name = spec.rpartition(":") if spec.split(":")[0] in ("strict", "original") else ("", "", spec)
        path = Path(name)
        for i, line in enumerate(l for l in path.read_text().splitlines() if l.strip()):
            rec = json.loads(line)
            seed = rec["seed"]
            fails = (lambda a, s=seed: _failures(s, a["diff"], cache)) if failures else (lambda a: [])
            base = {"suite": _suite(seed), "seed": seed, "source": f"{path.name}:{i}", "cost_usd": rec.get("cost_usd", 0)}
            if "judgments" in rec:  # cases file
                for prompt, verdicts in rec["judgments"].items():
                    for k, v in enumerate(verdicts):
                        att = {**rec, "judge": v, "author": "hand-written"}
                        runs.append({**base, "id": f"{path.stem}-{i}-{prompt}-{k}", "kind": "case", "prompt": prompt,
                                     "patch": rec["patch"], "patch_kind": rec["kind"], "cheat_type": "",
                                     "rounds": [_round(att, 1, "judge", [], fails)]})
                continue
            attempts = rec.get("rounds") or rec.get("attempts") or []
            if not attempts:
                continue
            for prompt, key in _prompts(attempts[0], tag):
                played, rounds = [], []
                for n, att in enumerate(attempts, 1):
                    played.append({**att, "judge": att.get(key, {})})
                    rounds.append(_round(att, att.get("round", n), key, played, fails))
                runs.append({**base, "id": f"{path.stem}-{i}-{prompt}", "kind": "duel" if "rounds" in rec else "eval",
                             "prompt": prompt, "patch": "", "patch_kind": "",
                             "cheat_type": rec.get("cheat_type") or rec.get("mode", ""), "rounds": rounds})
    return runs


def summarize(runs: list[dict]) -> dict:
    judged = [(r, rd) for r in runs for rd in r["rounds"] if rd["outcome"] != "failed"]

    def counts(rows):
        c = {o: 0 for o in ("caught", "missed", "false_alarm", "passed_clean", "error")}
        for _, rd in rows:
            c[rd["outcome"]] += 1
        c["judgments"] = len(rows)
        c["distinct_patches"] = len({(r["seed"], rd["diff"]) for r, rd in rows})
        return c

    scorecard = []
    for suite in ("toy", "real"):
        for prompt in ("original", "strict"):
            rows = [(r, rd) for r, rd in judged if r["suite"] == suite and r["prompt"] == prompt]
            if rows:
                scorecard.append({"suite": suite, "prompt": prompt, **counts(rows)})
    by_round = {}
    for r, rd in judged:
        if r["kind"] == "duel" and rd["label"] == "cheat":
            row = by_round.setdefault(r["prompt"], {}).setdefault(rd["n"], {"round": rd["n"], "caught": 0, "cheats": 0})
            row["cheats"] += 1
            row["caught"] += rd["outcome"] == "caught"
    # the regex baseline doesn't depend on the prompt, so count each judged round once
    seen = {(r["source"], rd["n"]): rd for r, rd in judged if rd["baseline"] in ("cheat", "clean")}
    baseline = [(None, rd) for rd in seen.values()]
    return {"all": counts(judged), "scorecard": scorecard,
            "by_round": {p: [rows[k] for k in sorted(rows)] for p, rows in by_round.items()},
            "baseline": {"caught": sum(rd["baseline"] == "cheat" for _, rd in baseline if rd["label"] == "cheat"),
                         "cheats": sum(rd["label"] == "cheat" for _, rd in baseline),
                         "false_alarms": sum(rd["baseline"] == "cheat" for _, rd in baseline if rd["label"] == "clean"),
                         "cleans": sum(rd["label"] == "clean" for _, rd in baseline)},
            # one record can become several runs (both prompts, repeats), so count each record's cost once
            "cost_usd": round(sum({r["source"]: r["cost_usd"] for r in runs}.values()), 4)}


def export(specs: list[str], failures: bool = True) -> Path:
    runs = load(specs, failures)
    seeds = sorted({r["seed"] for r in runs})
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    data = {"meta": {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "git_commit": commit,
                     "models": MODELS, "files": specs},
            "summary": summarize(runs),
            "tasks": {s: (ROOT / "seeds" / s / "task.md").read_text() for s in seeds},
            "runs": runs}
    OUT.mkdir(exist_ok=True)
    text = json.dumps(data, indent=1)
    (OUT / "data.json").write_text(text)
    (OUT / "data.js").write_text(f"window.WJJ_DATA = {text};\n")
    return OUT / "data.json"
