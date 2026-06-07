---
name: diagnose
description: Disciplined diagnosis loop for hard bugs and performance regressions in StudyCore. Follows reproduce → minimise → hypothesise → instrument → fix → regression-test. Use when user says "diagnose this", "debug this", "something is broken", "tests are failing", or describes a performance regression. Do NOT use for trivial syntax errors or when the fix is obvious from the error message.
---

# Diagnose

A discipline for hard bugs in the StudyCore codebase. Skip phases only when explicitly justified.

## Phase 1 — Build a feedback loop

**This is the skill.** Everything else is mechanical. If you have a fast, deterministic pass/fail signal for the bug, you will find the cause. If you don't have one, no amount of staring at code will save you.

Spend disproportionate effort here. **Be aggressive. Be creative. Refuse to give up.**

### Ways to construct a feedback loop

Try in this order:

1. **Failing test** — write a test that reproduces the bug through a public API.
2. **Curl / HTTP script** — against the running FastAPI dev server (`localhost:8000`).
3. **CLI invocation** — run a Python script with fixture input.
4. **UI script** — use Playwright to drive the frontend and assert on DOM/console.
5. **Replay a captured trace** — saved network request / payload / event log.
6. **Throwaway harness** — spin up a minimal subset (one service, mocked DB) that exercises the bug.
7. **Property / fuzz loop** — if the bug is "sometimes wrong", run random inputs.
8. **Bisection** — if bug appeared between commits, use `git bisect`.
9. **Differential loop** — run same input through old vs new version, diff outputs.

Build the right feedback loop, and the bug is 90% fixed.

### Iterate on the loop

- Can I make it faster? (skip unrelated init, narrow scope)
- Can I make the signal sharper? (assert on specific symptom, not "didn't crash")
- Can I make it more deterministic? (pin time, seed RNG, freeze network)

A 30-second flaky loop is barely better than no loop. A 2-second deterministic loop is a debugging superpower.

### Non-deterministic bugs

The goal is a **higher reproduction rate**. Loop the trigger 100×, parallelise, add stress, narrow timing windows. A 50%-flake bug is debuggable; 1% is not — keep raising the rate.

### Cannot build a loop?

Stop and say so explicitly. List what you tried. Ask the user for: (a) access to the environment, (b) a captured artifact (HAR, log dump), or (c) permission to add temporary instrumentation.

**Do not proceed to Phase 2 without a loop.**

## Phase 2 — Reproduce

Run the loop. Watch the bug appear.

- [ ] The loop produces the failure mode the **user** described — not a different failure nearby.
- [ ] The failure is reproducible across multiple runs (or at a high enough rate).
- [ ] Exact symptom captured (error message, wrong output, slow timing).

Do not proceed until you reproduce the bug.

## Phase 3 — Hypothesise

Generate **3–5 ranked hypotheses** before testing any of them.

Each hypothesis must be **falsifiable**: state the prediction it makes.

> Format: "If <X> is the cause, then <changing Y> will make the bug disappear / <changing Z> will make it worse."

**Show the ranked list to the user before testing.** They often have domain knowledge that re-ranks instantly.

## Phase 4 — Instrument

Each probe must map to a specific prediction from Phase 3. **Change one variable at a time.**

Tool preference:

1. **Debugger / REPL** — one breakpoint beats ten logs.
2. **Targeted logs** at the boundaries that distinguish hypotheses.
3. Never "log everything and grep".

**Tag every debug log** with a unique prefix, e.g. `[DEBUG-a4f2]`. Cleanup at the end becomes a single grep.

**Performance regressions:** logs are usually wrong. Establish a baseline measurement first (timing harness, profiler, query plan), then bisect. Measure first, fix second.

## Phase 5 — Fix + regression test

Write the regression test **before the fix** — but only if there is a **correct seam** for it.

A correct seam is one where the test exercises the **real bug pattern** as it occurs at the call site. If the only available seam is too shallow, a regression test there gives false confidence.

**If no correct seam exists, that itself is the finding.** The codebase architecture is preventing the bug from being locked down. Flag this for architecture improvement.

If a correct seam exists:

1. Turn the minimised repro into a failing test.
2. Watch it fail.
3. Apply the fix.
4. Watch it pass.
5. Re-run the Phase 1 feedback loop against the original scenario.

## Phase 6 — Cleanup + post-mortem

Required before declaring done:

- [ ] Original repro no longer reproduces
- [ ] Regression test passes (or absence of seam is documented)
- [ ] All `[DEBUG-...]` instrumentation removed
- [ ] Throwaway prototypes deleted
- [ ] Correct hypothesis stated in commit message

**Then ask: what would have prevented this bug?** If the answer involves architectural change, flag it for `improve-codebase-architecture` after the fix.
