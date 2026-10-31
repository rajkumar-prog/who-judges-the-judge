"""Balanced patch sets for the real-repo cases: correct fixes, incomplete fixes and cheats.

Each file under cases/<seed>/ is one patch with a KIND (correct, incomplete or cheat), in the same
FILE/OLD/NEW format as patches/. Every patch is judged with both prompts, `repeat` times each, so
we can see whether the judge accepts correct fixes that look different from upstream, rejects
honest-but-incomplete ones, catches cheats, and gives the same answer twice.
"""
import runpy
from dataclasses import asdict

from . import baseline, judge as judge_mod
from .duel import outcome
from .run import label
from .llm import LLM
from .workspace import ROOT, Workspace

CASES = ROOT / "cases"
PROMPTS = {"original": judge_mod.SYSTEM, "strict": judge_mod.STRICT}


def patches() -> list[tuple[str, str]]:
    """(seed, patch name) for every case patch."""
    if not CASES.is_dir():
        return []
    return sorted((d.name, p.stem) for d in CASES.iterdir() if d.is_dir() for p in d.glob("*.py"))


def load(seed: str, name: str) -> dict:
    return runpy.run_path(str(CASES / seed / f"{name}.py"))


def apply(ws: Workspace, name: str) -> dict:
    p = load(ws.seed, name)
    path = ws.path / p["FILE"]
    text = path.read_text()
    if text.count(p["OLD"]) != 1:
        raise ValueError(f"cases/{ws.seed}/{name}.py: OLD must appear exactly once in {p['FILE']}")
    path.write_text(text.replace(p["OLD"], p["NEW"]))
    return p


def judge_case(seed: str, name: str, repeat: int = 1, judge_client=None) -> dict:
    llm = LLM("baseten", client=judge_client)
    with Workspace(seed) as ws:
        p = apply(ws, name)
        visible, hidden = ws.run_tests(), ws.run_hidden()
        diff, touched, context = ws.diff(), ws.touched_files(), ws.changed_sources()
        rec = {"seed": seed, "patch": name, "kind": p["KIND"], "diff": diff,
               "visible_passed": visible.passed, "hidden_passed": hidden.passed,
               "label": label(visible.passed, hidden.passed, touched),
               "baseline": asdict(baseline.check(diff, touched)), "judgments": {}}
        if visible.passed:
            for prompt, system in PROMPTS.items():
                rec["judgments"][prompt] = [
                    asdict(judge_mod.judge(llm, ws.task(), diff, visible.output, system=system, context=context))
                    for _ in range(repeat)]
    rec["cost_usd"] = round(llm.usage.cost("baseten"), 5)
    return rec


def summarize(records: list[dict]) -> dict:
    """Per prompt: outcome counts over every judgment, plus how many patches got the same verdict
    on every repeat. Distinct patches and judgments are counted separately."""
    out = {"patches": len(records), "by_kind": {}, "prompts": {}}
    for r in records:
        out["by_kind"][r["kind"]] = out["by_kind"].get(r["kind"], 0) + 1
    for prompt in PROMPTS:
        counts, stable, judged = {}, 0, 0
        for r in records:
            verdicts = r["judgments"].get(prompt, [])
            if not verdicts:
                continue
            judged += 1
            stable += len({v["verdict"] for v in verdicts}) == 1
            for v in verdicts:
                o = outcome({"label": r["label"], "judge": v})
                counts[o] = counts.get(o, 0) + 1
        out["prompts"][prompt] = {"judgments": sum(counts.values()), "outcomes": counts,
                                  "stable_patches": stable, "judged_patches": judged}
    out["cost_usd"] = round(sum(r["cost_usd"] for r in records), 4)
    return out


def markdown(s: dict, records: list[dict]) -> str:
    def cell(r, prompt):
        vs = [v["verdict"] for v in r["judgments"].get(prompt, [])]
        return "/".join(vs) or "-"
    rows = "".join(f"| {r['seed']} | {r['patch']} | {r['kind']} | {r['label']} | {cell(r, 'original')} "
                   f"| {cell(r, 'strict')} | {r['baseline'].get('verdict')} |\n" for r in records)
    lines = [f"## Real-repo cases ({s['patches']} distinct patches, ${s['cost_usd']})\n",
             "| seed | patch | kind | hidden tests say | original judge | strict judge | regex |",
             "|---|---|---|---|---|---|---|", rows]
    for prompt, p in s["prompts"].items():
        lines.append(f"- {prompt}: {p['judgments']} judgments, outcomes {p['outcomes']}, "
                     f"same verdict on every repeat for {p['stable_patches']}/{p['judged_patches']} patches")
    return "\n".join(lines) + "\n"
