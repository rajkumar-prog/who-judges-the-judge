# Step 1 spike kit

Goal by **Tue Oct 27, 6 PM CT**: know (a) what one judge call costs, (b) whether Muse Code runs headless reliably.

## 0. Today
- Submit Baseten and Modal credit forms (capped at 2,000 / 1,000 people). Claim Meta credits when the link opens (card required; set a Spend Limit).

## 1. Spark Open judge ping
    pip install openai pytest
    BASETEN_API_KEY=... python spike/spark_open_ping.py
Expect `"verdict": "cheat"` (the diff weakens an assertion). Note tokens and cost.
The second check must print `"tool_calling": true`: the fixer agent loop depends on it.

Then the hosted reference judge (Meta Model API):

    MODEL_API_KEY=... python spike/spark_open_ping.py --meta

If `muse-spark-1.3` is rejected, check the model list in the Meta docs and set `META_MODEL`.
If the base URL 404s, take it from Baseten's quickstart and set BASETEN_BASE_URL.

## 2. Muse Code headless fix
    muse --version && muse exec --help      # confirm flags exist before trusting the script
    META_API_KEY=... ./spike/muse_headless.sh
The agent works in a temp copy of `seeds/toy`; `hidden/toy` is never copied in. Outputs land in `spike/out/` (git-ignored).
Run it 3 times. Record per run: exit code, wall time, steps/tokens, visible pass, hidden pass, touched tests.

Env var note: a third-party Muse Code guide says `META_API_KEY`; the event page says `MODEL_API_KEY` for the API. Try both if auth fails.

## Runtime rule (CV bot in #questions, 2026-10-26)
Muse Code used only while developing does not count; the submitted project must call Meta models at runtime.
The Spark Open judge already satisfies this. Muse Code (or your own Muse Spark loop) is the agent under test.

## Kill-switch (Tue 6 PM CT)
Go with Muse Code only if 3/3 runs finish without prompts or hangs and produce a diff.
Otherwise: write your own flag-then-redo loop on the Muse Spark API.
