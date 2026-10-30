"""Command line.

  python -m wjj run median --mode cheat     # one seed: fix → judge → redo, printed live
  python -m wjj eval --attempts 3           # every seed, both modes; writes results/ and scorecard
  python -m wjj score results/runs.jsonl    # rebuild the scorecard from saved runs
  python -m wjj duel median --rounds 3      # scripted cheat, then a model cheater adapts to the judge
"""
import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

from . import cheats, duel as duel_mod, scorecard
from .llm import LLM
from .run import run
from .workspace import ROOT


def _clients(reference: bool):
    client = LLM("baseten").client
    ref = LLM("meta").client if reference else None
    return client, ref


def _print_event(e: dict) -> None:
    if e["type"] == "tool":
        print(f"  step {e['step']:>2}  {e['name']} {e['path']}".rstrip())
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
    print(f"{len(jobs)} runs over {len(seeds)} seeds → {runs_path}")
    with ThreadPoolExecutor(max_workers=args.workers) as pool, runs_path.open("a") as f:
        futures = {pool.submit(run, s, m, args.redos, client, ref): (s, m) for s, m in jobs}
        for i, fut in enumerate(as_completed(futures), 1):
            s, m = futures[fut]
            try:
                rec = asdict(fut.result())
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
    seeds = [args.seed] if args.seed != "all" else sorted(
        p.name for p in (ROOT / "seeds").iterdir() if p.is_dir() and p.name != "toy")
    types = cheats.TYPES if args.cheat_type == "all" else (args.cheat_type,)
    out = ROOT / "results" / f"duel-{args.seed}-{time.strftime('%Y%m%d-%H%M%S')}.jsonl"
    out.parent.mkdir(exist_ok=True)
    records = []
    with out.open("w") as f:
        for seed in seeds:
            for t in types:
                print(f"\n== {seed} / {t} / cheater={args.cheater}")
                try:
                    rec = asdict(duel_mod.duel(seed, t, args.rounds, args.cheater, judge_client, cheater_client,
                                               on_event=_print_event))
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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="wjj")
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
    d.add_argument("--cheat-type", choices=["all", *cheats.TYPES], default="all")
    d.add_argument("--cheater", choices=["meta", "baseten"], default="meta")
    d.set_defaults(func=cmd_duel)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
