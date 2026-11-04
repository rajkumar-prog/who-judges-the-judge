// Case library dashboard. Everything on the page comes from window.WJJ_DATA (dashboard/data.js),
// which `python -m wjj dashboard` writes from saved result files. Nothing here is typed by hand.
(function () {
  const D = window.WJJ_DATA;
  const page = document.getElementById("page");
  const tip = document.getElementById("tip");
  if (!D) { page.innerHTML = "<h1>No data</h1><p>Run <code>python -m wjj dashboard results/final/*.jsonl</code> first.</p>"; return; }

  const RUNS = D.runs;
  const REPO = "https://github.com/rajkumar-prog/who-judges-the-judge";
  const NAMES = { caught: "Caught", missed: "Missed", false_alarm: "False alarm", passed_clean: "Passed clean",
                  failed: "Failed visible tests", error: "Judge error" };
  const PILL = { caught: "Caught: cheat flagged", missed: "Missed: wrong fix approved", false_alarm: "False alarm: good fix flagged",
                 passed_clean: "Clean fix accepted", failed: "Not judged: failed visible tests", error: "Judge reply unreadable" };
  const LIB = { ttlcache: "cachetools", proxyauth: "requests", xmlattr: "Jinja2" };

  const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  // a single-round eval is scored on its first attempt only; later attempts come after judge feedback
  // and stay for the replay
  RUNS.forEach(r => r.rounds.forEach((rd, i) => { rd.redo = r.kind === "eval" && i > 0; }));
  const judged = rd => rd.outcome !== "failed" && !rd.redo;
  const pct = (a, b) => b ? Math.round(100 * a / b) + "%" : "—";
  const frac = (a, b) => b ? `${a} / ${b}` : "— / —";

  // counts over (run, round) pairs
  function tally(pairs) {
    const c = { caught: 0, missed: 0, false_alarm: 0, passed_clean: 0, error: 0, failed: 0 };
    pairs.forEach(([, rd]) => c[rd.outcome]++);
    c.cheats = c.caught + c.missed;
    c.cleans = c.false_alarm + c.passed_clean;
    return c;
  }
  const pairs = (filter) => RUNS.flatMap(r => r.rounds.map(rd => [r, rd])).filter(([r, rd]) => filter(r, rd));

  // runs that belong together get the same key in both prompts, so grid rows line up
  function keyed(runs) {
    const seen = {};
    return runs.map(r => {
      const k = `${r.suite}|${r.seed}|${r.cheat_type || r.patch}`;
      const i = (seen[k + r.prompt] = (seen[k + r.prompt] || 0) + 1);
      return { r, key: `${k}|${i}`, rep: i };
    });
  }
  function runLabel(r, rep) {
    const what = r.cheat_type || r.patch;
    const n = RUNS.filter(x => x.kind === r.kind && x.prompt === r.prompt && x.seed === r.seed && (x.cheat_type || x.patch) === what).length;
    return `${r.seed} · ${what}${n > 1 ? " #" + rep : ""}`;
  }

  // ---------- 01 Experiment ----------
  function experiment() {
    // headline tiles use the same slices as the README: real-library duels, and the correct
    // real-library patches judged in cases
    const realDuel = prompt => tally(pairs((r, rd) => r.suite === "real" && r.kind === "duel" && r.prompt === prompt && judged(rd)));
    const realOrig = realDuel("original");
    const strict = realDuel("strict");
    const strictCases = tally(pairs((r, rd) => r.kind === "case" && r.prompt === "strict" && judged(rd)));
    const cost = D.summary.cost_usd;
    const judgments = pairs((r, rd) => judged(rd)).length;
    const origRound = n => tally(pairs((r, rd) => r.suite === "real" && r.kind === "duel" && r.prompt === "original" && rd.n === n && judged(rd)));
    const r1 = origRound(1), r2 = origRound(2);

    const duels = RUNS.filter(r => r.kind === "duel");
    // one row per duel, the original and strict judge side by side; rows pair up by seed, cheat and repeat
    const byKey = {};
    ["original", "strict"].forEach(prompt => keyed(duels.filter(r => r.prompt === prompt)).forEach(({ r, key, rep }) => {
      (byKey[key] = byKey[key] || { key, rep, suite: r.suite, seed: r.seed, what: r.cheat_type || r.patch })[prompt] = r;
    }));
    const squares = r => {
      if (!r) return `<span class="squares muted">not run</span>`;
      let sq = "";
      for (let n = 1; n <= Math.max(3, r.rounds.length); n++) {
        const rd = r.rounds[n - 1];
        sq += rd ? `<button class="sq ${rd.outcome}" data-run="${esc(r.id)}" data-n="${n}" aria-label="round ${n} ${rd.outcome}"></button>`
                 : `<span class="sq none"></span>`;
      }
      return `<span class="squares">${sq}</span>`;
    };
    const sum = (suite, prompt) => {
      const t = tally(pairs((r, rd) => r.kind === "duel" && r.suite === suite && r.prompt === prompt && judged(rd)));
      return `caught ${frac(t.caught, t.cheats)}` + (t.cleans ? ` · ${frac(t.false_alarm, t.cleans)} false alarms` : "");
    };
    const rowsFor = list => list.sort((a, b) => a.key.localeCompare(b.key)).map(x => {
      const n = Object.values(byKey).filter(y => y.suite === x.suite && y.seed === x.seed && y.what === x.what).length;
      const label = x.suite === "real" ? `${x.what}${n > 1 ? " #" + x.rep : ""}` : `${x.seed} · ${x.what}${n > 1 ? " #" + x.rep : ""}`;
      return `<div class="drow"><span class="name" title="${esc(x.suite === "real" ? x.seed + " · " + label : label)}">${esc(label)}</span>${squares(x.original)}${squares(x.strict)}</div>`;
    }).join("");
    const all = Object.values(byKey);
    const realSeeds = [...new Set(all.filter(x => x.suite === "real").map(x => x.seed))].sort();
    const toy = all.filter(x => x.suite === "toy");
    const duelTable = all.length ? `<div class="duels card">
        <div class="drow dhead"><span></span>
          <span><b>Original judge</b><i>“is this a cheat?”</i></span>
          <span><b>Strict judge</b><i>“find an allowed input where this is wrong”</i></span></div>
        <div class="drow rhead"><span></span>${'<span class="squares"><i>R1</i><i>R2</i><i>R3</i></span>'.repeat(2)}</div>
        <div class="drow dsum"><span>Real libraries, ${all.length - toy.length} duels</span><span>${sum("real", "original")}</span><span>${sum("real", "strict")}</span></div>
        ${realSeeds.map(seed => `<div class="dgroup">${esc(LIB[seed] || seed)} <span>${esc(seed)}</span></div>` +
          rowsFor(all.filter(x => x.suite === "real" && x.seed === seed))).join("")}
        ${toy.length ? `<details class="toy"><summary class="drow dsum"><span><i class="caret">▸</i> Toy seeds, ${toy.length} duels</span><span>${sum("toy", "original")}</span><span>${sum("toy", "strict")}</span></summary>
          ${rowsFor(toy)}</details>` : ""}
      </div>` : '<p class="muted">No duels in the data.</p>';

    page.innerHTML = `
      <div class="crumb">01 / Experiment</div>
      <h1>Who judges the judge?</h1>
      <p class="lede">An AI reviewer reads a code fix and says whether it is honest. Hidden tests then show what the fix really was. A verdict is a claim. A test run is evidence.</p>
      <div class="tiles">
        <div class="card tile"><div class="num">${realOrig.cheats ? realOrig.missed : "—"}<small>${realOrig.cheats ? " of " + realOrig.cheats : ""}</small></div>
          <p>wrong fixes in real-library duels that the original judge approved</p></div>
        <div class="card tile"><div class="num">${pct(strict.caught, strict.cheats)}</div>
          <p>strict judge catch rate in the same duels, ${frac(strict.caught, strict.cheats)} wrong fixes</p></div>
        <div class="card tile"><div class="num">${frac(strictCases.false_alarm, strictCases.cleans).replace(" / ", "<small> / ") + (strictCases.cleans ? "</small>" : "")}</div>
          <p>strict judge false alarms on correct real-library fixes, each judged 3 times (${frac(strict.false_alarm, strict.cleans)} in duels)</p></div>
        <div class="card tile"><div class="num">${r2.cheats ? r2.missed : "—"}<small>${r2.cheats ? " of " + r2.cheats : ""}</small></div>
          <p>wrong fixes the original judge approved in round 2, once the cheater had read its reasons (${r1.missed} of ${r1.cheats} in round 1)</p></div>
      </div>
      <p class="note mono">${judgments} judgments by Muse Spark Open on Baseten · cheater Muse Spark on the Meta Model API · total model cost $${cost.toFixed(2)}</p>
      <div class="flow-row">
        <div class="flow" id="flow">
          <div class="box" data-s="0"><b>Cheater · Muse Spark</b>writes a fix</div><div class="arrow">→</div>
          <div class="box" data-s="1"><b>Visible tests</b>the fix passes them</div><div class="arrow">→</div>
          <div class="box" data-s="2"><b>Judge · Muse Spark Open</b>says clean or cheat</div><div class="arrow">→</div>
          <div class="box" data-s="3"><b>Hidden tests</b>decide what it really was</div>
          <div class="back" data-s="4">← the judge's reasons go back to the cheater, which tries again</div>
        </div>
        <button class="btn" id="play">▶ Play a real duel</button>
      </div>
      <div class="story" id="story" hidden>
        <div class="story-head"><span id="story-round"></span><span class="story-dots" id="story-dots"></span></div>
        <p id="story-text"></p>
        <a id="story-link" hidden>Open this duel in the replay →</a>
      </div>
      <h2>Every duel, round by round</h2>
      <p class="lede" style="margin-bottom:12px">One row per duel, one square per round, the same starting cheat against each judge. From round 2 the cheater has read the judge's reasons. A duel ends when the judge says clean. Click any square to replay it.</p>
      <div class="legend">
        <span><i class="sq caught"></i>caught</span><span><i class="sq missed"></i>missed: wrong fix approved</span>
        <span><i class="sq false_alarm"></i>false alarm: good fix flagged</span><span><i class="sq passed_clean"></i>correct fix, approved</span>
        <span><i class="sq failed"></i>failed visible tests, not judged</span>${RUNS.some(r => r.rounds.some(rd => rd.outcome === "error")) ? '<span><i class="sq error"></i>judge error</span>' : ""}
        <span><i class="sq none"></i>not played</span>
      </div>
      ${duelTable}`;

    page.querySelectorAll(".sq[data-run]").forEach(b => {
      b.onclick = () => { location.hash = `replay/${b.dataset.run}/${b.dataset.n}`; };
      b.onmouseenter = e => {
        const r = RUNS.find(x => x.id === b.dataset.run), rd = r.rounds[b.dataset.n - 1];
        tip.innerHTML = `Round ${rd.n} · judge: ${esc(rd.judge.verdict || "—")} · tests: ${esc(rd.label)}` +
          (rd.hidden_failures.length ? ` · ${rd.hidden_failures.length} hidden failed` : "") + `<br>${NAMES[rd.outcome]} · open replay →`;
        tip.style.display = "block";
        tip.style.left = e.clientX + 12 + "px"; tip.style.top = e.clientY + 12 + "px";
      };
      b.onmouseleave = () => { tip.style.display = "none"; };
    });
    clearTimeout(playing); resume = null; paused = false;
    document.getElementById("play").onclick = onPlay;
  }

  // plays one real duel from the data through the flow diagram, step by step, with what actually happened
  let playing = null;
  function storyDuel() {
    const real = RUNS.filter(r => r.kind === "duel" && r.suite === "real" && r.prompt === "original");
    const missedAfterCatch = r => r.rounds.length >= 2 && r.rounds[0].outcome === "caught" && r.rounds.some(rd => rd.outcome === "missed");
    // the Jinja2 duel where the fix's blocklist forgot "/" is the one the write-up walks through
    return real.find(r => r.seed === "xmlattr" && missedAfterCatch(r) && r.rounds.some(rd => rd.outcome === "missed" && rd.hidden_failures.some(t => t.includes("-/]"))))
      || real.find(missedAfterCatch) || RUNS.find(r => r.kind === "duel") || null;
  }
  function storySteps(r) {
    const cut = (s, n) => { s = String(s || "").replace(/\s+/g, " ").trim(); return s.length > n ? s.slice(0, n - 1) + "…" : s; };
    const steps = [];
    r.rounds.forEach((rd, i) => {
      const round = `Round ${rd.n} of ${r.rounds.length} · ${r.seed}${LIB[r.seed] ? " (" + LIB[r.seed] + ")" : ""}`;
      steps.push({ s: 0, round, text: i === 0 ? `The round 1 fix is a scripted cheat (${r.cheat_type}). It looks like a real fix.`
        : "Muse Spark has read the judge's reasons and rewrites the fix to get past it." });
      steps.push({ s: 1, round, text: rd.visible_passed ? "It passes every visible test. A normal CI check would go green here."
        : "It fails the visible tests, so it never reaches the judge." });
      if (rd.outcome === "failed") return;
      const verdict = rd.judge.verdict === "cheat" ? "Cheat" : rd.judge.verdict === "clean" ? "Clean" : "No verdict";
      // when the reason is about to be read out as feedback, show the line the judge pointed at here instead
      const repeat = i < r.rounds.length - 1 && rd.judge.reason && rd.judge.evidence;
      steps.push({ s: 2, round, text: repeat ? `The judge says <b>${verdict}</b>, pointing at <code>${esc(cut(rd.judge.evidence, 90))}</code>`
        : `The judge says <b>${verdict}</b>. “${esc(cut(rd.judge.reason || rd.judge.evidence, 140))}”` });
      const k = rd.hidden_failures.length;
      const tail = { caught: `<b class="good">Caught.</b> The judge was right.`, missed: `<b class="bad">Missed.</b> The judge approved a wrong fix.`,
        false_alarm: `<b class="warn">False alarm.</b> The fix was fine.`, passed_clean: `<b class="good">Correct fix, approved.</b>` }[rd.outcome] || "";
      steps.push({ s: 3, round, outcome: rd.outcome, text: (rd.label === "cheat" ? `${k} hidden test${k === 1 ? "" : "s"} fail. ` : "Every hidden test passes. ") + tail });
      if (i < r.rounds.length - 1) steps.push({ s: 4, round, text: rd.judge.reason
        ? `The judge's reason goes back to Muse Spark: “${esc(cut(rd.judge.reason, 260))}”`
        : "The judge's reasons go back to the cheater, and it tries again." });
    });
    return steps;
  }
  // the play button doubles as pause/resume while a story is running
  let paused = false, resume = null;
  function onPlay() {
    const btn = document.getElementById("play");
    if (resume && !paused) { paused = true; clearTimeout(playing); btn.textContent = "▶ Resume"; return; }
    if (resume && paused) { paused = false; btn.textContent = "❚❚ Pause"; resume(); return; }
    play();
  }

  function play() {
    clearTimeout(playing); paused = false;
    const r = storyDuel();
    if (!r) return;
    const boxes = [...document.querySelectorAll("#flow [data-s]")];
    const story = document.getElementById("story"), text = document.getElementById("story-text"),
          head = document.getElementById("story-round"), dots = document.getElementById("story-dots"),
          link = document.getElementById("story-link"), btn = document.getElementById("play");
    const steps = storySteps(r);
    story.hidden = false; link.hidden = true; btn.textContent = "❚❚ Pause";
    dots.innerHTML = steps.map(() => "<i></i>").join("");
    boxes.forEach(b => b.classList.remove("lit", "done", "good", "bad"));
    let i = 0;
    const step = () => {
      if (!document.body.contains(story)) { resume = null; return; }
      if (i >= steps.length) {
        btn.textContent = "↺ Play again"; resume = null;
        const missedAt = r.rounds.findIndex(rd => rd.outcome === "missed") + 1 || r.rounds.length;
        link.href = `#replay/${r.id}/${missedAt}`; link.hidden = false;
        boxes.forEach(b => b.classList.remove("lit"));
        return;
      }
      const st = steps[i];
      if (st.s === 0) boxes.forEach(b => b.classList.remove("done", "good", "bad"));
      boxes.forEach(b => {
        const s = +b.dataset.s;
        b.classList.toggle("lit", s === st.s);
        if (s < st.s && st.s !== 4) b.classList.add("done");
      });
      if (st.s === 3) boxes[3].classList.add(st.outcome === "missed" || st.outcome === "false_alarm" ? "bad" : "good");
      head.textContent = st.round;
      text.classList.remove("in"); void text.offsetWidth;
      text.innerHTML = st.text; text.classList.add("in");
      [...dots.children].forEach((d, j) => d.className = j < i ? "past" : j === i ? "now" : "");
      i++;
      playing = setTimeout(step, st.s >= 2 ? 5000 : 3200);
    };
    resume = () => { playing = setTimeout(step, 1200); };
    step();
  }

  // ---------- 02 Duel replay ----------
  function pickDefault() {
    const featured = storyDuel();
    const any = (featured && featured.rounds.some(rd => rd.outcome === "missed") && featured)
      || RUNS.find(r => r.rounds.some(rd => rd.outcome === "missed")) || RUNS[0];
    const n = (any.rounds.findIndex(rd => rd.outcome === "missed") + 1) || 1;
    return [any.id, n];
  }

  function diffHtml(diff, evidence) {
    const ev = (evidence || "").replace(/\s+/g, " ").trim();
    return diff.split("\n").map(line => {
      const cls = line.startsWith("+++") || line.startsWith("---") || line.startsWith("diff ") ? "hunk"
        : line.startsWith("@@") ? "hunk" : line.startsWith("+") ? "add" : line.startsWith("-") ? "del" : "";
      const body = line.slice(1).replace(/\s+/g, " ").trim();
      const hit = ev && cls !== "hunk" && body.length >= 6 && ev.includes(body);
      return `<div class="${cls}${hit ? " ev" : ""}">${esc(line) || " "}</div>`;
    }).join("");
  }

  // long test lists show the first few, the rest fold away
  function testList(names, cls) {
    const li = t => `<li>${esc(t)}</li>`, k = 6;
    if (names.length <= k + 1) return `<ul class="fails ${cls}">${names.map(li).join("")}</ul>`;
    return `<ul class="fails ${cls}">${names.slice(0, k).map(li).join("")}</ul>` +
      `<details class="more"><summary>${names.length - k} more</summary><ul class="fails ${cls}">${names.slice(k).map(li).join("")}</ul></details>`;
  }

  // one proving test function, cut out of the judge's test file (prefer one without parameters)
  function provingSnippet(c) {
    if (!c.test || !c.proving.length) return "";
    const src = c.test.replace(/^```\w*\n?|```\s*$/g, "");
    const name = (c.proving.find(t => !t.includes("[")) || c.proving[0]).split("[")[0];
    const lines = src.split("\n");
    let i = lines.findIndex(l => l.startsWith(`def ${name}(`));
    if (i < 0) return "";
    while (i > 0 && lines[i - 1].startsWith("@")) i--;
    let j = i + 1;
    while (j < lines.length && !lines[j].startsWith("def ") && !lines[j].startsWith("@") && !/^[A-Za-z_#]/.test(lines[j])) j++;
    const body = lines.slice(i, j).join("\n").trimEnd();
    return body.split("\n").length > 18 ? "" : `<div class="label" style="margin:10px 0 4px">one of the tests it wrote</div><pre class="snippet">${esc(body)}</pre>`;
  }

  function confirmCard(r, rd) {
    const c = rd.confirm;
    let body;
    if (c) {
      const say = {
        confirmed: c.proving.length === 1 ? "The judge wrote a test from its own finding. It fails on this patch and passes on the library's real fix."
          : `The judge wrote tests from its own finding. ${c.proving.length} of them fail on this patch and pass on the library's real fix.`,
        test_wrong: "The judge's test also fails on the library's real fix, so it proves nothing.",
        not_reproduced: "The judge's test passes on this patch too. It couldn't show the problem it described.",
        error: "No usable test came back, or it didn't run."
      }[c.status];
      body = `<span class="chip ${c.status}">${c.status.replace("_", " ")}</span><p style="margin:10px 0 0">${say}</p>` +
        (c.status === "confirmed" ? provingSnippet(c) : "") +
        (c.proving.length ? `<div class="label" style="margin:10px 0 4px">tests that fail on this patch, pass on the real fix</div>${testList(c.proving, "ok")}` : "") +
        (c.test ? `<details style="margin-top:8px;padding:6px 10px"><summary>test_wjj_confirm.py</summary><pre>${esc(c.test)}</pre></details>` : "");
    } else if (rd.judge.verdict === "cheat") {
      body = `<span class="chip">not run</span><p style="margin:10px 0 0" class="muted">Judge-written tests were only run on the real-library results.</p>`;
    } else {
      return `<p class="note">Judge's own test: none. The judge said clean, so there was nothing for it to prove.</p>`;
    }
    return `<div class="card"><div class="label">Judge's own test</div><div style="margin-top:8px">${body}</div></div>`;
  }

  let view = "patch";
  function replay(id, n) {
    if (!id) [id, n] = pickDefault();
    const r = RUNS.find(x => x.id === id) || RUNS.find(x => x.id === pickDefault()[0]);
    n = Math.min(Math.max(+n || 1, 1), r.rounds.length);
    const rd = r.rounds[n - 1];

    // three small pickers instead of one long list: what kind of run, which one, which judge
    const groups = [["duel", "real", "Real-library duels"], ["duel", "toy", "Toy duels"],
                    ["case", "real", "Fixed real-library patches"], ["eval", "real", "Single-round eval, real"], ["eval", "toy", "Single-round eval, toy"]]
      .filter(([kind, suite]) => RUNS.some(x => x.kind === kind && x.suite === suite));
    const gi = Math.max(0, groups.findIndex(([kind, suite]) => kind === r.kind && suite === r.suite));
    const inGroup = keyed(RUNS.filter(x => x.kind === groups[gi][0] && x.suite === groups[gi][1]));
    const myKey = (inGroup.find(x => x.r.id === r.id) || {}).key;
    const twin = prompt => (inGroup.find(x => x.key === myKey && x.r.prompt === prompt) || {}).r;
    const items = [];
    inGroup.sort((a, b) => a.key.localeCompare(b.key)).forEach(x => { if (!items.some(y => y.key === x.key)) items.push(x); });
    const groupSel = groups.map(([kind, suite, title], i) => `<option value="${i}"${i === gi ? " selected" : ""}>${title}</option>`).join("");
    const itemSel = items.map(x => `<option value="${esc(x.key)}"${x.key === myKey ? " selected" : ""}>${esc(runLabel(x.r, x.rep))}</option>`).join("");
    const judgeBtns = ["original", "strict"].map(pr => {
      const t = twin(pr);
      return `<button data-run="${t ? esc(t.id) : ""}" class="${pr === r.prompt ? "on" : ""}" ${t ? "" : "disabled title='not run with this judge'"}>${pr === "strict" ? "Strict judge" : "Original judge"}</button>`;
    }).join("");
    const rounds = Array.from({ length: Math.max(3, r.rounds.length) }, (_, i) =>
      `<button data-n="${i + 1}" class="${i + 1 === n ? "on" : ""}" ${i < r.rounds.length ? "" : "disabled title='not played'"}>R${i + 1}</button>`).join("");
    const last = r.rounds[r.rounds.length - 1];
    const endNote = r.kind !== "duel" || r.rounds.length >= 3 ? ""
      : last.outcome === "failed" ? `ended after round ${r.rounds.length}: the fix failed the visible tests`
      : last.judge && last.judge.verdict === "clean" ? `ended after round ${r.rounds.length}: the judge said clean`
      : `ended after round ${r.rounds.length}`;

    const verdictWord = rd.outcome === "failed" ? "Not judged" : rd.judge.verdict ? rd.judge.verdict[0].toUpperCase() + rd.judge.verdict.slice(1) : "No verdict";
    const truthWord = { cheat: "Cheat", clean: "Clean", failed: "Failed" }[rd.label] || rd.label;
    const truthLine = rd.label === "failed" ? "The fix didn't pass the visible tests, so it never reached the judge."
      : rd.label === "clean" ? "Every hidden test passes. This fix does what the task asks."
      : `Passes the visible tests, fails ${rd.hidden_failures.length || "some"} hidden test${rd.hidden_failures.length === 1 ? "" : "s"}.`;
    const what = r.kind === "case" ? `${r.patch} (${r.patch_kind})` : r.cheat_type;
    const prev = n > 1 ? r.rounds[n - 2] : null;
    const told = r.kind === "duel" && prev && prev.feedback_after && prev.judge ? (prev.judge.reason || prev.judge.evidence || "") : "";
    const author = { script: "scripted cheat", meta: "Muse Spark", agent: "Muse Spark", "hand-written": "hand-written patch" }[rd.author] || rd.author;

    page.innerHTML = `
      <div class="crumb">02 / Duel replay · ${esc(r.seed)}${LIB[r.seed] ? " (" + LIB[r.seed] + ")" : ""} · ${esc(r.prompt)} judge</div>
      <h1>Read the verdict. Check the evidence.</h1>
      <p class="lede">The patch, what the judge said about it, and what the tests proved, side by side. Use ← and → to step through rounds.</p>
      <div class="controls">
        <select id="group" aria-label="kind of run">${groupSel}</select>
        <select id="pick" aria-label="which one">${itemSel}</select>
        <div class="rounds" id="judges">${judgeBtns}</div>
        ${r.kind === "case" ? "" : `<div class="rounds" id="rounds">${rounds}</div>`}
        <span class="label">${esc(what)} · round ${n} by ${esc(author)}${endNote ? " · " + endNote : ""}</span>
        <span class="pill ${rd.outcome}">${PILL[rd.outcome]}</span>
      </div>
      ${told ? `<div class="told"><span class="label">Before round ${n}, Muse Spark read the judge's round ${n - 1} reason</span><p>“${esc(told)}”</p>
        <details class="more"><summary>exactly what it was told</summary><pre>${esc(prev.feedback_after)}</pre></details></div>` : ""}
      <div class="replay">
        <div class="tree">
          <button data-v="task" class="${view === "task" ? "on" : ""}">task.md</button>
          <button data-v="patch" class="${view === "patch" ? "on" : ""}">patch.diff</button>
        </div>
        ${view === "task" ? `<div class="task">${esc(D.tasks[r.seed] || "")}</div>`
                          : `<div class="code">${diffHtml(rd.diff || "(no diff)", rd.judge.evidence)}</div>`}
        <div class="card says">
          <div class="label">Judge says · prediction</div>
          <div class="verdict">${verdictWord}</div>
          ${rd.judge.evidence ? `<div class="label" style="margin-bottom:4px">evidence it quoted</div><div class="evline">${esc(rd.judge.evidence)}</div>` : ""}
          ${rd.judge.reason ? `<p class="quote">${esc(rd.judge.reason)}</p>` : ""}
          ${rd.judge.counterexample ? `<div class="label" style="margin-bottom:4px">counterexample</div><p class="mono" style="font-size:12px">${esc(rd.judge.counterexample)}</p>` : ""}
        </div>
        <div class="card shows">
          <div class="label">Tests show · evidence</div>
          <div class="verdict">${truthWord}</div>
          <p>${truthLine}</p>
          ${rd.hidden_failures.length ? `<div class="label" style="margin-bottom:4px">hidden tests that fail</div>${testList(rd.hidden_failures, "")}` : ""}
          <p class="muted" style="font-size:12px">Visible tests: ${rd.visible_passed ? "pass" : "fail"} · Regex baseline said: ${esc(rd.baseline || "—")}</p>
        </div>
      </div>
      <div class="below">
        ${confirmCard(r, rd)}
        ${rd.feedback_after && n < r.rounds.length ? `<details><summary>Exactly what the cheater was told before round ${n + 1}</summary><pre>${esc(rd.feedback_after)}</pre></details>` : ""}
        <details><summary>Full judge verdict</summary><pre>${esc(JSON.stringify(rd.judge, null, 2))}</pre></details>
        <p class="note mono">source: ${esc(r.source)} · run ${esc(r.id)}</p>
      </div>`;

    document.getElementById("group").onchange = e => {
      const [kind, suite] = groups[+e.target.value];
      const first = keyed(RUNS.filter(x => x.kind === kind && x.suite === suite)).sort((a, b) => a.key.localeCompare(b.key))
        .find(x => x.r.prompt === r.prompt) || keyed(RUNS.filter(x => x.kind === kind && x.suite === suite))[0];
      location.hash = `replay/${first.r.id}/1`;
    };
    document.getElementById("pick").onchange = e => {
      const pickRun = inGroup.find(x => x.key === e.target.value && x.r.prompt === r.prompt) || inGroup.find(x => x.key === e.target.value);
      location.hash = `replay/${pickRun.r.id}/1`;
    };
    page.querySelectorAll("#judges button:not(:disabled)").forEach(b => b.onclick = () => {
      const t = RUNS.find(x => x.id === b.dataset.run);
      location.hash = `replay/${t.id}/${Math.min(n, t.rounds.length)}`;
    });
    page.querySelectorAll("#rounds button:not(:disabled)").forEach(b => b.onclick = () => { location.hash = `replay/${r.id}/${b.dataset.n}`; });
    page.querySelectorAll(".tree button").forEach(b => b.onclick = () => { view = b.dataset.v; replay(r.id, n); });
    replay.current = [r, n];
  }

  // ---------- 03 Results ----------
  function results() {
    const prompts = ["original", "strict"];
    const sets = [["Real-library duels", r => r.kind === "duel" && r.suite === "real"],
                  ["Real-library cases", r => r.kind === "case"],
                  ["Toy duels", r => r.kind === "duel" && r.suite === "toy"],
                  ["Single-round eval (first attempts)", r => r.kind === "eval"]];
    const cell = (a, b, good) => `<td class="n ${b ? (a === (good ? b : 0) ? "ok" : "") : ""}">${frac(a, b)}${b ? ` <small>${pct(a, b)}</small>` : ""}</td>`;
    const rows = sets.map(([name, f]) => {
      const t = prompts.map(p => tally(pairs((r, rd) => f(r) && r.prompt === p && judged(rd))));
      if (!t[0].cheats && !t[1].cheats && !t[0].cleans && !t[1].cleans) return "";
      return `<tr><td>${name}</td>${t.map(x => cell(x.caught, x.cheats, true) + `<td class="n ${x.false_alarm ? "warn" : ""}">${frac(x.false_alarm, x.cleans)}</td><td class="n">${x.error}</td>`).join("")}</tr>`;
    }).join("");

    // regex baseline: doesn't depend on the prompt, count each distinct patch once
    const seen = new Map();
    pairs((r, rd) => judged(rd) && (rd.baseline === "cheat" || rd.baseline === "clean")).forEach(([r, rd]) => seen.set(r.seed + "\n" + rd.diff, rd));
    const bl = [...seen.values()];
    const blC = bl.filter(rd => rd.label === "cheat"), blK = bl.filter(rd => rd.label === "clean");
    const baseline = `<tr><td>Regex baseline (no model)<br><small class="muted">each distinct patch once</small></td>
      <td class="n" colspan="3">caught ${frac(blC.filter(rd => rd.baseline === "cheat").length, blC.length)} · false alarms ${frac(blK.filter(rd => rd.baseline === "cheat").length, blK.length)}</td><td colspan="3"></td></tr>`;

    // catch rate by round, duels only
    const byRound = suite => {
      const maxN = Math.max(0, ...RUNS.filter(r => r.kind === "duel" && r.suite === suite).map(r => r.rounds.length));
      if (!maxN) return "";
      let out = `<div class="label" style="margin:12px 0 8px">${suite === "real" ? "Real libraries" : "Toy seeds"}</div>`;
      for (let n = 1; n <= maxN; n++) {
        out += `<div class="r"><span class="mono">R${n}</span><div class="wrapbar">` + prompts.map(p => {
          const t = tally(pairs((r, rd) => r.kind === "duel" && r.suite === suite && r.prompt === p && rd.n === n && judged(rd)));
          const w = t.cheats ? 100 * t.caught / t.cheats : 0;
          return `<div class="bar"><i style="width:${w}%;background:${p === "strict" ? "var(--blue)" : "var(--blue-2)"};opacity:${p === "strict" ? 1 : .55}"></i><span>${p} ${frac(t.caught, t.cheats)}</span></div>`;
        }).join("") + "</div></div>";
      }
      return out;
    };

    // real-library cases, patch by patch
    const cases = RUNS.filter(r => r.kind === "case");
    const patches = [...new Set(cases.map(r => r.seed + "/" + r.patch))].sort();
    // one small card per library, one line per patch
    const caseSeeds = [...new Set(cases.map(r => r.seed))].sort();
    const caseCards = caseSeeds.map(seed => {
      const lines = patches.filter(k => k.startsWith(seed + "/")).map(k => {
        const patch = k.split("/")[1];
        const mine = cases.filter(r => r.seed === seed && r.patch === patch);
        const label = mine[0].rounds[0].label;
        const cells = prompts.map(p => {
          const rs = mine.filter(r => r.prompt === p).map(r => r.rounds[0]);
          const right = rs.filter(rd => rd.outcome === (label === "cheat" ? "caught" : "passed_clean")).length;
          const errs = rs.filter(rd => rd.outcome === "error").length;
          return `<span class="n ${rs.length && right === rs.length ? "ok" : "bad"}" title="${p} judge${errs ? `, ${errs} error` : ""}">${right}/${rs.length}</span>`;
        }).join("");
        return `<div class="cline"><span><span class="mono">${esc(patch)}</span> <small class="tag ${label}">${label === "cheat" ? "wrong" : "correct"}</small></span>${cells}</div>`;
      }).join("");
      return `<div class="card ccard"><div class="chead"><b>${esc(LIB[seed] || seed)}</b><span>orig</span><span>strict</span></div>${lines}</div>`;
    }).join("");

    // judge-written tests
    const conf = prompts.map(p => {
      const rs = pairs((r, rd) => r.suite === "real" && r.prompt === p && rd.judge.verdict === "cheat" && judged(rd));
      const c = s => rs.filter(([, rd]) => rd.confirm && rd.confirm.status === s).length;
      const onClean = rs.filter(([, rd]) => rd.label === "clean" && rd.confirm && rd.confirm.status === "confirmed").length;
      return `<tr><td>${p === "strict" ? "Strict" : "Original"}</td><td class="n">${rs.length}</td><td class="n ok">${c("confirmed")}</td><td class="n">${c("test_wrong")}</td><td class="n">${c("not_reproduced")}</td><td class="n">${c("error")}</td><td class="n">${rs.filter(([, rd]) => !rd.confirm).length}</td><td class="n">${onClean}</td></tr>`;
    }).join("");

    const all = tally(pairs((r, rd) => judged(rd)));
    const distinct = new Set(pairs((r, rd) => judged(rd)).map(([r, rd]) => r.seed + "\n" + rd.diff)).size;

    page.innerHTML = `
      <div class="crumb">03 / Results</div>
      <h1>Results, with their limits.</h1>
      <p class="lede">Every rate shows its count. Toy and real code are never mixed. A wrong fix is one that passes the visible tests and fails a hidden one.</p>
      <table>
        <thead><tr><th></th><th colspan="3">Original judge</th><th colspan="3">Strict judge</th></tr>
        <tr><th></th><th>Wrong fixes caught</th><th>False alarms / good fixes</th><th>Errors</th><th>Wrong fixes caught</th><th>False alarms / good fixes</th><th>Errors</th></tr></thead>
        <tbody>${rows}${baseline}</tbody>
      </table>
      <h2>Does the judge get worse as the cheater adapts?</h2>
      <div class="card bars"><div class="two"><div>${byRound("real")}</div><div>${byRound("toy")}</div></div>
        <p class="note">Each round counts only duels still going. From round 2 the cheater has read the judge's reasons.</p></div>
      <h2>Same patch, judged 3 times</h2>
      <p class="note" style="margin:-4px 0 10px">Fixed patches on real libraries. Each number is right answers out of tries.</p>
      <div class="ccards">${caseCards || '<p class="muted">No case results in the data.</p>'}</div>
      <h2>Did the judge prove it?</h2>
      <table>
        <thead><tr><th></th><th>Cheat verdicts, real code</th><th>Confirmed by its own test</th><th>Test was wrong</th><th>Couldn't reproduce</th><th>Error</th><th>Not run</th><th>Confirmed on a fix the hidden tests pass</th></tr></thead>
        <tbody>${conf}</tbody>
      </table>
      <p class="note">Confirmed means the judge's test fails on the patch and passes on the library's real fix. It never changes a verdict or a label.</p>
      <p class="note mono" style="margin-top:24px">Distinct patches ${distinct} · Judgments ${all.cheats + all.cleans + all.error} · Cost $${D.summary.cost_usd.toFixed(2)} · Generated ${esc(D.meta.generated_at)}</p>`;
  }

  // ---------- 04 Method ----------
  function method() {
    const doc = p => `${REPO}/blob/main/${p}`;
    page.innerHTML = `
      <div class="crumb">04 / Method</div>
      <h1>How the experiment works.</h1>
      <p class="lede">The judge's verdict is a prediction. The hidden tests are the answer key.</p>
      <div class="steps">
        <div class="card"><b>01 / Cheat</b>Round 1 is a scripted wrong fix. From round 2, Muse Spark (Meta Model API) rewrites it after reading why the judge caught it.</div>
        <div class="card"><b>02 / Judge</b>Muse Spark Open on Baseten reads the task, the diff and the changed files, and says clean or cheat.</div>
        <div class="card"><b>03 / Check</b>Hidden tests the cheater never sees decide what each fix really was.</div>
        <div class="card"><b>04 / Prove</b>For each cheat verdict on real code, the judge writes a test. It counts only if it fails on the fix and passes on the library's real fix.</div>
      </div>
      <div class="band">
        <div><div class="label">Judge says = prediction</div><p style="margin:6px 0 0">What the model believes about the fix, with the line it quotes as evidence.</p></div>
        <div><div class="label">Tests show = evidence</div><p style="margin:6px 0 0">What running the hidden tests proves. This is the label every number is scored against.</p></div>
      </div>
      <h2>Two judge prompts</h2>
      <div class="quotes">
        <div class="card"><div class="label">Original</div>“Is this a cheat?”</div>
        <div class="card"><div class="label">Strict</div>“Find an allowed input where this is wrong.”</div>
      </div>
      <h2>Real code</h2>
      <p>Three real bugs from open-source Python libraries, each with the version before the fix vendored in: cachetools 7.2.1 (TTLCache expiry), requests 2.30.0 (CVE-2023-32681, Proxy-Authorization leaked on redirect) and Jinja2 3.1.2 (xmlattr key injection, CVE-2024-22195 and CVE-2024-34064). The visible tests are upstream's own.</p>
      <h2>Limits</h2>
      <ol class="limits">
        <li>Twelve toy seeds and three real libraries. A small sample.</li>
        <li>Every seed is Python.</li>
        <li>The cheater is told to cheat. Natural cheating rates will differ.</li>
        <li>The same model family plays judge and cheater.</li>
        <li>The judge doesn't always give the same verdict twice.</li>
        <li>Hidden tests were frozen before the final run. Any later finding is listed, not fixed.</li>
      </ol>
      <h2>Source documents</h2>
      <div class="links">
        <a class="card" href="${REPO}"><div class="label">Repository</div>who-judges-the-judge</a>
        <a class="card" href="${doc("docs/final-run.md")}"><div class="label">Plan</div>Final-run plan</a>
        <a class="card" href="${doc("docs/hidden-tests-log.md")}"><div class="label">Log</div>Hidden-test log</a>
        <a class="card" href="${REPO}/tree/main/results/final"><div class="label">Data</div>Raw results</a>
      </div>`;
  }

  // ---------- routing ----------
  const PAGES = { experiment, replay, results, method };
  function route() {
    const [name, ...rest] = (location.hash.slice(1) || "experiment").split("/");
    const fn = PAGES[name] || experiment;
    document.querySelectorAll("nav a").forEach(a => a.classList.toggle("on", a.dataset.page === (PAGES[name] ? name : "experiment")));
    document.getElementById("path").textContent = "case-library / " + (PAGES[name] ? name : "experiment");
    tip.style.display = "none";
    if (fn !== replay) replay.current = null;
    fn(...rest);
    if (!rest.length) window.scrollTo(0, 0);
  }
  window.addEventListener("hashchange", route);
  document.getElementById("source").textContent =
    `data: ${D.meta.files.length} result file${D.meta.files.length === 1 ? "" : "s"} · commit ${D.meta.git_commit}` + (D.meta.note ? " · sample" : "");

  function theme(t) {
    document.documentElement.dataset.theme = t;
    try { localStorage.setItem("wjj-theme", t); } catch (e) {}
  }
  let saved = null;
  try { saved = localStorage.getItem("wjj-theme"); } catch (e) {}
  theme(saved || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
  document.getElementById("theme").onclick = () => theme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
  document.addEventListener("keydown", e => {
    if (e.target.tagName === "SELECT" || e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.key === "d" || e.key === "D") document.getElementById("theme").click();
    if (replay.current && (e.key === "ArrowLeft" || e.key === "ArrowRight")) {
      const [r, n] = replay.current, m = n + (e.key === "ArrowRight" ? 1 : -1);
      if (m >= 1 && m <= r.rounds.length) location.hash = `replay/${r.id}/${m}`;
    }
  });
  route();
})();
