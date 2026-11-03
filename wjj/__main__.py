"""Command line.

  python -m wjj run median --mode cheat     # one seed: fix → judge → redo, printed live
  python -m wjj eval --attempts 3           # every seed, both modes; writes results/ and scorecard
  python -m wjj score results/runs.jsonl    # rebuild the scorecard from saved runs
  python -m wjj duel median --rounds 3      # scripted cheat, then a model cheater adapts to the judge
  python -m wjj regrade results/duel-x.jsonl  # re-check saved diffs against today's hidden tests
  python -m wjj probe                       # judge each hand-written cheat with and without its decoy comment
  python -m wjj cases --repeat 2            # judge every real-repo case patch with both prompts
  python -m wjj dashboard strict:results/duel-x.jsonl ...  # export results for the dashboard page
  python -m wjj rejudge results/a.jsonl ...  # rescore saved diffs with the strict judge prompt
"""
import argparse
import json
import os
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

from . import cases as cases_mod, cheats, confirm as confirm_mod, dashboard as dashboard_mod, duel as duel_mod, probe as probe_mod, rejudge as rejudge_mod, scorecard
from .llm import LLM, BudgetExceeded
from .run import run
from .workspace import ROOT


def _clients(reference: bool):
    client = LLM("baseten").client
    ref = LLM("meta").client if reference else None
    return client, ref


def _print_event(e: dict) -> None:
    if e["type"] == "tool":
        print(f"  step {e['step']:>2}  {e['name']} {e['path']}".rstrip())
    elif e["type"] == "silent":
        print(f"  step {e['step']:>2}  (no tool call: ended {e['finish_reason']}, {e['completion_tokens']} tokens)")
    elif e["type"] == "attempt":
        print(f"  → ground truth: {e['label']}   judge: {e['judge']}   baseline: {e['baseline']}")
        if e.get("evidence"):
            print(f"    evidence: {e['evidence']}")
    elif e["type"] == "round":
        print(f"\n  round {e['n']}")
    elif e["type"] == "redo":
        print(f"\n  judge said cheat, redo #{e['n']}")


def cmd_run(args) -> int:
    client, ref = _clients(args.reference)
    print(f"seed={args.seed} mode={args.mode}")
    rec = run(args.seed, args.mode, args.redos, client, ref, on_event=_print_event)
    print(f"\nfinal: {rec.final_label}   attempts: {len(rec.attempts)}   cost: ${rec.cost_usd}")
    out = ROOT / "results" / f"run-{args.seed}-{args.mode}-{time.strftime('%Y%m%d-%H%M%S')}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(asdict(rec), indent=2))
    (out.parent / "latest.json").write_text(out.read_text())
    print(f"full transcript: {out.relative_to(ROOT)} (also results/latest.json)")
    return 0


def cmd_eval(args) -> int:
    client, ref = _clients(args.reference)
    seeds = args.seeds.split(",") if args.seeds else sorted(
        p.name for p in (ROOT / "seeds").iterdir() if p.is_dir() and p.name != "toy")
    jobs = [(s, m) for s in seeds for m in ("honest", "cheat") for _ in range(args.attempts)]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    runs_path = out / "runs.jsonl"
    if args.resume and runs_path.exists():
        # finish a run that stopped early: skip the (seed, mode) runs already saved
        done = Counter((r["seed"], r["mode"]) for r in (json.loads(l) for l in runs_path.read_text().splitlines() if l.strip()))
        left = []
        for job in jobs:
            if done[job] > 0:
                done[job] -= 1
            else:
                left.append(job)
        print(f"resuming: {len(jobs) - len(left)} already saved")
        jobs = left
    print(f"{len(jobs)} runs over {len(seeds)} seeds → {runs_path}")
    with ThreadPoolExecutor(max_workers=args.workers) as pool, runs_path.open("a") as f:
        futures = {pool.submit(run, s, m, args.redos, client, ref): (s, m) for s, m in jobs}
        for i, fut in enumerate(as_completed(futures), 1):
            s, m = futures[fut]
            try:
                rec = asdict(fut.result())
            except BudgetExceeded:
                raise
            except Exception as e:
                print(f"[{i}/{len(jobs)}] {s} {m}: error {e}", file=sys.stderr)
                continue
            f.write(json.dumps(rec) + "\n")
            f.flush()
            a = rec["attempts"][0]
            print(f"[{i}/{len(jobs)}] {s:10} {m:6} truth={a['label']:6} judge={a['judge'].get('verdict', '-')}")
    return _write_score(runs_path, out)


def _write_score(runs_path: Path, out: Path) -> int:
    records = [json.loads(line) for line in runs_path.read_text().splitlines() if line.strip()]
    s = scorecard.score(records)
    (out / "scorecard.json").write_text(json.dumps(s, indent=2))
    md = scorecard.markdown(s)
    (out / "scorecard.md").write_text(md)
    print("\n" + md)
    return 0


def cmd_score(args) -> int:
    p = Path(args.runs)
    return _write_score(p, p.parent)


def cmd_duel(args) -> int:
    judge_client = LLM("baseten").client
    cheater_client = judge_client if args.cheater == "baseten" else LLM(args.cheater).client
    # "all" means the toy suite; the real-repo seeds are run by name, since the scripted
    # cheats only edit their tests and teach nothing there.
    seeds = [args.seed] if args.seed != "all" else sorted(
        p.name for p in (ROOT / "seeds").iterdir()
        if p.is_dir() and p.name != "toy" and p.name not in cases_mod.seeds())
    types = cheats.TYPES if args.cheat_type == "all" else (args.cheat_type,)
    if args.cheat_type in cheats.patch_types():
        seeds = [s for s in seeds if s in cheats.patched_seeds(args.cheat_type)]
    out = ROOT / "results" / f"duel-{args.seed}-{_stamp()}.jsonl"
    out.parent.mkdir(exist_ok=True)
    records = []
    with out.open("w") as f:
        for seed in seeds:
            for t in types:
                print(f"\n== {seed} / {t} / cheater={args.cheater}")
                try:
                    rec = asdict(duel_mod.duel(seed, t, args.rounds, args.cheater, judge_client, cheater_client,
                                               on_event=_print_event))
                except BudgetExceeded:
                    raise
                except Exception as e:
                    print(f"  error: {e}", file=sys.stderr)
                    continue
                f.write(json.dumps(rec) + "\n")
                f.flush()
                records.append(rec)
    md = duel_mod.markdown(duel_mod.summarize(records))
    print("\n" + md)
    out.with_suffix(".md").write_text(md)
    print(f"saved {out.relative_to(ROOT)}")
    return 0


def _check_setup() -> None:
    """Hidden tests on the real-library seeds need these. Without them every round there would be
    labelled failed, so stop instead of saving wrong results."""
    import importlib.util
    missing = [m for m in ("markupsafe", "urllib3", "idna", "charset_normalizer", "certifi")
               if importlib.util.find_spec(m) is None]
    if missing:
        raise SystemExit(f"Missing {', '.join(missing)}. Run: pip install -r requirements.txt")
    for seed, lib in (("ttlcache", "cachetools"), ("proxyauth", "requests"), ("xmlattr", "jinja2")):
        if not (ROOT / "seeds" / seed / lib).is_dir():
            raise SystemExit(f"seeds/{seed}/{lib} is missing. Run: python scripts/fetch_libs.py")


def cmd_regrade(args) -> int:
    _check_setup()
    src = Path(args.duels)
    records = [json.loads(line) for line in src.read_text().splitlines() if line.strip()]
    records, changes = duel_mod.regrade(records)
    out = src.with_name(src.stem + "-regraded.jsonl")
    out.write_text("".join(json.dumps(r) + "\n" for r in records))
    for c in changes:
        print(f"  {c['seed']:10} {c['cheat_type']:15} round {c['round']}: {c['before']} -> {c['after']}")
    if all("rounds" in r for r in records):
        md = duel_mod.markdown(duel_mod.summarize(records))
    else:  # an eval runs.jsonl
        md = scorecard.markdown(scorecard.score(records))
    out.with_suffix(".md").write_text(md)
    print(f"\n{len(changes)} rounds changed\n\n{md}\nsaved {out}")
    return 0


def cmd_probe(args) -> int:
    client = LLM("baseten").client
    types = cheats.patch_types() if args.cheat_type == "all" else [args.cheat_type]
    records = []
    try:
        for t in types:
            for seed in cheats.patched_seeds(t):
                rec = probe_mod.probe(t, seed, client)
                records.append(rec)
                print(f"  {t:15} {seed:10} hidden={rec['plain']['label']:6} judge={rec['plain']['judge'].get('verdict')}"
                      f"  with comment={rec['decoy']['judge'].get('verdict')}{'  FLIPPED' if rec['flipped'] else ''}")
    except BudgetExceeded as e:
        print(f"\n{e}; saving the {len(records)} finished", file=sys.stderr)
    out = ROOT / "results" / f"probe-{_stamp()}.jsonl"
    out.parent.mkdir(exist_ok=True)
    out.write_text("".join(json.dumps(r) + "\n" for r in records))
    md = probe_mod.markdown(probe_mod.summarize(records), records)
    out.with_suffix(".md").write_text(md)
    print("\n" + md + f"\nsaved {out.relative_to(ROOT)}")
    return 0


def cmd_cases(args) -> int:
    client = LLM("baseten").client
    records = []
    try:
        for seed, name in cases_mod.patches():
            rec = cases_mod.judge_case(seed, name, args.repeat, client)
            records.append(rec)
            verdicts = lambda p: "/".join(v["verdict"] for v in rec["judgments"].get(p, [])) or "-"
            print(f"  {seed:10} {name:20} {rec['kind']:10} hidden={rec['label']:6} "
                  f"original={verdicts('original')}  strict={verdicts('strict')}")
    except BudgetExceeded as e:
        print(f"\n{e}; saving the {len(records)} finished", file=sys.stderr)
    out = ROOT / "results" / f"cases-{_stamp()}.jsonl"
    out.parent.mkdir(exist_ok=True)
    out.write_text("".join(json.dumps(r) + "\n" for r in records))
    md = cases_mod.markdown(cases_mod.summarize(records), records)
    out.with_suffix(".md").write_text(md)
    print("\n" + md + f"\nsaved {out.relative_to(ROOT)}")
    return 0


def cmd_dashboard(args) -> int:
    if not args.fast:
        _check_setup()
    out = dashboard_mod.export(args.files, failures=not args.fast)
    s = json.loads(out.read_text())["summary"]["all"]
    print(f"{s['distinct_patches']} distinct patches, {s['judgments']} judgments -> {out.relative_to(ROOT)} and data.js")
    return 0


def cmd_rejudge(args) -> int:
    client = LLM("baseten").client
    everything, cost = [], 0.0
    for name in args.files:
        src = Path(name)
        records = [json.loads(line) for line in src.read_text().splitlines() if line.strip()]
        todo = sum(a.get("judge_strict", {}).get("verdict") in (None, "error") for _, a in rejudge_mod.graded(records))
        print(f"{src.name}: {todo} diffs to judge")
        cost += rejudge_mod.rejudge(records, client, args.workers,
                                    on_done=lambda i, n: print(f"  {i}/{n}", end="\r", flush=True))
        out = src if src.stem.endswith("-rejudged") else src.with_name(src.stem + "-rejudged.jsonl")
        out.write_text("".join(json.dumps(r) + "\n" for r in records))
        print(f"  saved {out}")
        everything += records
    md = rejudge_mod.markdown(rejudge_mod.compare(everything), cost)
    print("\n" + md)
    report = ROOT / "results" / f"rejudge-{time.strftime('%Y%m%d-%H%M%S')}.md"
    report.parent.mkdir(exist_ok=True)
    report.write_text(md)
    return 0


def cmd_confirm(args) -> int:
    client = LLM("baseten").client
    for name in args.files:
        src = Path(name)
        records = confirm_mod.load(src)
        out = src.with_name(src.stem + "-confirmed.jsonl")
        print(f"{src.name}: {sum(1 for _ in confirm_mod.jobs(records))} cheat verdicts to confirm")
        records = confirm_mod.load(src)
        try:
            cost = confirm_mod.confirm(records, client, args.workers,
                                       on_done=lambda i, n: print(f"  {i}/{n}", end="\r", flush=True))
        except BudgetExceeded as e:
            print(f"\n{e}; saving what finished", file=sys.stderr)
            cost = None
        out.write_text("".join(json.dumps(r) + "\n" for r in records))
        md = confirm_mod.markdown(confirm_mod.summarize(records))
        out.with_suffix(".md").write_text(md)
        print(f"\n{md}" + (f"cost ${cost:.2f}, " if cost is not None else "") + f"saved {out}")
    return 0


def _stamp() -> str:
    """Timestamp for result file names, tagged with the judge prompt so two runs started in the
    same second with different prompts never write the same file."""
    tag = "-strict" if os.environ.get("WJJ_JUDGE") == "strict" else ""
    return time.strftime("%Y%m%d-%H%M%S") + tag


def load_env(path: Path = ROOT / ".env") -> None:
    """Read KEY=VALUE lines from .env into the environment, without overriding anything already set."""
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            value = value.strip().strip("'\"")
            if value:
                os.environ.setdefault(key.strip(), value)


def main(argv=None) -> int:
    load_env()
    ap = argparse.ArgumentParser(prog="wjj")
    ap.add_argument("--strict-judge", action="store_true",
                    help="judge with the strict correctness prompt instead of the original one")
    ap.add_argument("--budget", type=float, help="stop making model calls once this run has spent this many dollars")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("seed")
    r.add_argument("--mode", choices=["honest", "cheat"], default="honest")
    r.add_argument("--redos", type=int, default=2)
    r.add_argument("--reference", action="store_true", help="also judge with hosted Muse Spark")
    r.set_defaults(func=cmd_run)
    e = sub.add_parser("eval")
    e.add_argument("--attempts", type=int, default=3, help="runs per seed per mode")
    e.add_argument("--seeds", default="", help="comma-separated; default all except toy")
    e.add_argument("--resume", action="store_true", help="skip runs already saved in --out (finish a run that stopped early)")
    e.add_argument("--redos", type=int, default=2)
    e.add_argument("--workers", type=int, default=4)
    e.add_argument("--reference", action="store_true")
    e.add_argument("--out", default="results")
    e.set_defaults(func=cmd_eval)
    s = sub.add_parser("score")
    s.add_argument("runs")
    s.set_defaults(func=cmd_score)
    d = sub.add_parser("duel")
    d.add_argument("seed", help="a seed name, or 'all'")
    d.add_argument("--rounds", type=int, default=3)
    d.add_argument("--cheat-type", choices=["all", *cheats.TYPES, *cheats.patch_types()], default="all")
    d.add_argument("--cheater", choices=["meta", "baseten"], default="meta")
    d.set_defaults(func=cmd_duel)
    g = sub.add_parser("regrade", help="re-run the current hidden tests on saved duel diffs (no model calls)")
    g.add_argument("duels")
    g.set_defaults(func=cmd_regrade)
    da = sub.add_parser("dashboard", help="export result files into dashboard/data.json for the page")
    da.add_argument("files", nargs="+", help="result files; prefix with strict: or original: if the file doesn't record its prompt")
    da.add_argument("--fast", action="store_true", help="skip re-running hidden tests to list failing test names")
    da.set_defaults(func=cmd_dashboard)
    ca = sub.add_parser("cases", help="judge every real-repo case patch with both prompts")
    ca.add_argument("--repeat", type=int, default=2, help="judgments per patch per prompt")
    ca.set_defaults(func=cmd_cases)
    pr = sub.add_parser("probe", help="judge each hand-written cheat with and without its decoy comment")
    pr.add_argument("--cheat-type", choices=["all", *cheats.patch_types()], default="all")
    pr.set_defaults(func=cmd_probe)
    cf = sub.add_parser("confirm", help="have the judge write a failing test for each saved cheat verdict, then run it")
    cf.add_argument("files", nargs="+")
    cf.add_argument("--workers", type=int, default=4)
    cf.set_defaults(func=cmd_confirm)
    rj = sub.add_parser("rejudge", help="rescore saved duel or eval diffs with the strict judge prompt")
    rj.add_argument("files", nargs="+")
    rj.add_argument("--workers", type=int, default=4)
    rj.set_defaults(func=cmd_rejudge)
    args = ap.parse_args(argv)
    if args.strict_judge:
        os.environ["WJJ_JUDGE"] = "strict"
    if args.budget is not None:
        os.environ["WJJ_BUDGET"] = str(args.budget)
    try:
        return args.func(args)
    except BudgetExceeded as e:
        print(f"\n{e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
