#!/usr/bin/env python3
"""Probe an uploaded fragment, atomic_gate_commit_v0.py, for cases where it lands or reports
something it should not.

The fragment is NOT in this repository (see NOTES.md for why). Pass its path; the script refuses
to run unless the file is byte-for-byte the one that was analysed.

    python3 -B attacks_gate.py /path/to/atomic_gate_commit_v0.py

FLAW means the fragment landed something it should have refused, or reported a state that is
not true. HOLDS means it behaved correctly, including by refusing loudly.
"""

import argparse
import hashlib
import importlib.util
import json
import multiprocessing
import os
import sys
import tempfile
import threading
from pathlib import Path

EXPECTED_SHA256 = "d45ef0286821a830aa7aea34326b0a207fadbde903a6824e26f38a9840a360a5"
APPROVE = {"decision": "APPROVE", "by": "human"}


def load(path, unchecked=False):
    digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256 and not unchecked:
        sys.exit(f"refusing: {path} has sha256 {digest}, not the analysed fragment {EXPECTED_SHA256}")
    spec = importlib.util.spec_from_file_location("fragment", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolves string annotations through sys.modules
    spec.loader.exec_module(module)
    return module


def workshop(g, root):
    motor = root / "motor.py"
    motor.write_text("print('motor')\n")
    seal = root / "motor_seal.json"
    seal.write_text(json.dumps({"motor_sha256": g.sha256_file(motor), "motor_pointer": "motor.py"}))
    return g.AtomicGatePaths(repo=root, kernel=root / "kernel", ledger=root / "ledger.jsonl",
                             runs_root=root / "runs", motor_path=motor, motor_seal_path=seal)


def lines(ledger):
    if not ledger.exists():
        return []
    return [json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]


def prepared(g, paths, run_id, events, decision=APPROVE):
    """A run that went through every step: motor check, decision, candidate."""
    sp = g.open_scratchpad(paths, run_id)
    sp.write_motor_hash_check(g.verify_motor_hash(paths)[1])
    sp.write_gate_decision(decision)
    sp.write_commit_candidate(events)
    return sp


def attempt(action):
    try:
        action()
    except Exception as err:
        return err
    return None


def result(flaw, evidence):
    return {"outcome": "FLAW" if flaw else "HOLDS", "evidence": evidence}


# --- what the gate lets through -----------------------------------------------------------

def reject_still_lands(g, paths):
    sp = prepared(g, paths, "r1", [{"change": 1}], decision={"decision": "REJECT", "by": "human"})
    err = attempt(lambda: g.commit_finalized_run(sp, paths.ledger, [{"change": 1}]))
    landed = bool(lines(paths.ledger))
    return result(landed, "a REJECT decision landed as GATE_RUN_LANDED" if landed else f"refused: {err}")


def candidate_not_bound(g, paths):
    sp = prepared(g, paths, "r1", [{"reviewed": "A"}])
    err = attempt(lambda: g.commit_finalized_run(sp, paths.ledger, [{"never_reviewed": "B"}]))
    rows = lines(paths.ledger)
    landed = rows[0]["staged_events"] if rows else None
    flaw = landed is not None and landed != [{"reviewed": "A"}]
    return result(flaw, f"candidate held A; the ledger received {landed}" if rows else f"refused: {err}")


def failed_motor_check_lands(g, paths):
    paths.motor_path.write_text("print('a different motor')\n")
    ok, detail = g.verify_motor_hash(paths)
    sp = g.open_scratchpad(paths, "r1")
    sp.write_motor_hash_check(detail)
    sp.write_gate_decision(APPROVE)
    sp.write_commit_candidate([{"change": 1}])
    err = attempt(lambda: g.commit_finalized_run(sp, paths.ledger, [{"change": 1}]))
    landed = bool(lines(paths.ledger))
    return result(not ok and landed,
                  f"verify_motor_hash said {detail['status']} ({detail.get('reason')}); "
                  + ("the run landed anyway" if landed else f"refused: {err}"))


def seal_pointer_ignored(g, paths):
    seal = json.loads(paths.motor_seal_path.read_text())
    seal["motor_pointer"] = "some/other/file.py"
    paths.motor_seal_path.write_text(json.dumps(seal))
    ok, detail = g.verify_motor_hash(paths)
    return result(ok, "the seal names some/other/file.py; the check of motor.py still PASSes" if ok
                  else f"check failed: {detail.get('reason')}")


def torn_decision_counts(g, paths):
    sp = g.open_scratchpad(paths, "r1")
    sp.write_motor_hash_check(g.verify_motor_hash(paths)[1])
    sp.path("gate_decision.json").write_text('{"decision": "APP')  # a crash mid-write
    sp.write_commit_candidate([{"change": 1}])
    err = attempt(lambda: g.commit_finalized_run(sp, paths.ledger, [{"change": 1}]))
    landed = bool(lines(paths.ledger))
    return result(landed, "a half-written gate_decision.json was accepted as a decision" if landed
                  else f"refused: {type(err).__name__}")


def self_written_approval(g, paths):
    # Whoever runs the process can write the human's decision file. Nothing records who wrote it.
    sp = g.open_scratchpad(paths, "r1")
    sp.write_motor_hash_check(g.verify_motor_hash(paths)[1])
    sp.write_gate_decision({"decision": "APPROVE", "by": "human", "note": "written by the process itself"})
    sp.write_commit_candidate([{"change": 1}])
    err = attempt(lambda: g.commit_finalized_run(sp, paths.ledger, [{"change": 1}]))
    landed = bool(lines(paths.ledger))
    return result(landed, "an APPROVE written by the process itself landed like a human's" if landed
                  else f"refused: {err}")


# --- what the status says ------------------------------------------------------------------

def committed_marker_trusted(g, paths):
    sp = prepared(g, paths, "r1", [{"change": 1}])
    g.commit_finalized_run(sp, paths.ledger, [{"change": 1}])
    paths.ledger.write_text("")  # the ledger loses the line (rewritten, restored from an old copy...)
    err = attempt(lambda: g.commit_finalized_run(sp, paths.ledger, [{"change": 1}]))
    missing = not g.ledger_contains_run_id(paths.ledger, "r1")
    silent = err is None
    return result(missing and silent and sp.status_label() == "COMMITTED",
                  f"status {sp.status_label()!r}, ledger contains the run: {not missing}; a re-commit "
                  + ("returned normally" if silent else f"refused: {err}"))


def rerun_after_abort_blocked(g, paths):
    run_id = g.stable_run_id("source-sha-1", "APPROVE")
    g.open_scratchpad(paths, run_id).mark_aborted("motor_missing")  # a transient cause, later fixed
    sp = prepared(g, paths, run_id, [{"change": 1}])
    err = attempt(lambda: g.commit_finalized_run(sp, paths.ledger, [{"change": 1}]))
    return result(err is not None,
                  f"same inputs give the same run_id {run_id} and directory; the retry fails: {err}" if err
                  else "the retry landed")


def rerun_after_commit_drops(g, paths):
    run_id = g.stable_run_id("source-sha-1", "APPROVE")
    g.commit_finalized_run(prepared(g, paths, run_id, [{"events": "A"}]), paths.ledger, [{"events": "A"}])
    sp2 = prepared(g, paths, run_id, [{"events": "B"}])
    err = attempt(lambda: g.commit_finalized_run(sp2, paths.ledger, [{"events": "B"}]))
    landed = [row["staged_events"] for row in lines(paths.ledger)]
    return result(err is None and landed == [[{"events": "A"}]],
                  f"second run {'returned as if it succeeded' if err is None else f'refused: {err}'}; "
                  f"the ledger holds {landed}")


def _concurrent_child(fragment_path, unchecked, root, run_id, barrier):
    g = load(fragment_path, unchecked)
    paths = workshop(g, Path(root))
    real_replace = os.replace

    def replace_after_both_have_read(src, dst):
        # Widens a window that exists anyway: both writers read the ledger before either replaces it.
        try:
            barrier.wait(3)
        except threading.BrokenBarrierError:
            pass
        return real_replace(src, dst)

    g.os.replace = replace_after_both_have_read
    sp = prepared(g, paths, run_id, [{"run": run_id}])
    g.commit_finalized_run(sp, paths.ledger, [{"run": run_id}])


def concurrent_lost_update(g, paths, fragment_path, unchecked):
    ctx = multiprocessing.get_context("fork")
    barrier = ctx.Barrier(2)
    procs = [ctx.Process(target=_concurrent_child, args=(fragment_path, unchecked, str(paths.repo), rid, barrier))
             for rid in ("c1", "c2")]
    for p in procs:
        p.start()
    for p in procs:
        p.join(30)
    both_committed = all(g.open_scratchpad(paths, rid).status_label() == "COMMITTED" for rid in ("c1", "c2"))
    kept = [row["run_id"] for row in lines(paths.ledger)]
    return result(both_committed and len(kept) < 2,
                  f"both runs report COMMITTED: {both_committed}; the ledger keeps {kept} (interleaving forced)")


def timestamps_without_zone(g, paths):
    stamp = g.now_iso()
    return result(not (stamp.endswith("Z") or "+" in stamp[10:] or "-" in stamp[10:]),
                  f"now_iso() gives {stamp!r}")


def edited_ledger_unnoticed(g, paths):
    sp = prepared(g, paths, "r1", [{"amount": 10}])
    g.commit_finalized_run(sp, paths.ledger, [{"amount": 10}])
    paths.ledger.write_text(paths.ledger.read_text().replace('"amount": 10', '"amount": 99'))
    recorded = json.loads(sp.path("COMMITTED.json").read_text())["ledger_sha256"]
    return result(sp.status_label() == "COMMITTED" and recorded != g.sha256_file(paths.ledger),
                  "ledger edited after landing; status still COMMITTED; the recorded ledger hash no longer "
                  "matches, but nothing in the module compares them")


# --- what I expected to hold ---------------------------------------------------------------

def crash_between_land_and_mark(g, paths):
    sp = prepared(g, paths, "r1", [{"change": 1}])
    g.atomic_append_ledger_lines(paths.ledger, [g.build_landed_line("r1", [{"change": 1}])])
    before = sp.status_label()
    g.commit_finalized_run(sp, paths.ledger, [{"change": 1}])
    count = sum(1 for row in lines(paths.ledger) if row["run_id"] == "r1")
    return result(not (before == "ORPHAN" and sp.status_label() == "COMMITTED" and count == 1),
                  f"status {before} -> {sp.status_label()}, run lines in ledger: {count}")


def rerun_is_idempotent(g, paths):
    sp = prepared(g, paths, "r1", [{"change": 1}])
    g.commit_finalized_run(sp, paths.ledger, [{"change": 1}])
    g.commit_finalized_run(sp, paths.ledger, [{"change": 1}])
    return result(len(lines(paths.ledger)) != 1, f"two commits of one run -> {len(lines(paths.ledger))} line(s)")


def aborted_run_refuses(g, paths):
    sp = prepared(g, paths, "r1", [{"change": 1}])
    sp.mark_aborted("test")
    err = attempt(lambda: g.commit_finalized_run(sp, paths.ledger, [{"change": 1}]))
    return result(err is None, f"refused: {err}" if err else "an aborted run landed")


def missing_decision_refuses(g, paths):
    sp = g.open_scratchpad(paths, "r1")
    sp.write_commit_candidate([{"change": 1}])
    err = attempt(lambda: g.commit_finalized_run(sp, paths.ledger, [{"change": 1}]))
    return result(err is None, f"refused: {err}" if err else "a run without any decision landed")


CASES = [
    # (id, case, predicted before running: FLAW or HOLDS)
    ("G1", reject_still_lands, "FLAW"),
    ("G2", candidate_not_bound, "FLAW"),
    ("G3", failed_motor_check_lands, "FLAW"),
    ("G4", seal_pointer_ignored, "FLAW"),
    ("G5", committed_marker_trusted, "FLAW"),
    ("G6", rerun_after_abort_blocked, "FLAW"),
    ("G7", rerun_after_commit_drops, "FLAW"),
    ("G8", concurrent_lost_update, "FLAW"),
    ("G9", torn_decision_counts, "FLAW"),
    ("G10", timestamps_without_zone, "FLAW"),
    ("G11", crash_between_land_and_mark, "HOLDS"),
    ("G12", rerun_is_idempotent, "HOLDS"),
    ("G13", aborted_run_refuses, "HOLDS"),
    ("G14", missing_decision_refuses, "HOLDS"),
    ("G15", edited_ledger_unnoticed, "FLAW"),
    ("G16", self_written_approval, "FLAW"),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("fragment")
    parser.add_argument("--unchecked", action="store_true",
                        help="run against a file that is not the analysed fragment (e.g. a patched copy); "
                             "results are then not about the fragment")
    args = parser.parse_args()
    fragment = os.path.abspath(args.fragment)
    g = load(fragment, args.unchecked)
    flaws = 0
    for ident, case, predicted in CASES:
        with tempfile.TemporaryDirectory() as tmp:
            paths = workshop(g, Path(tmp))
            try:
                if case is concurrent_lost_update:
                    row = case(g, paths, fragment, args.unchecked)
                else:
                    row = case(g, paths)
            except Exception as err:  # a crash of the harness itself is reported, not hidden
                row = {"outcome": "CRASH", "evidence": f"{type(err).__name__}: {err}"}
        flaws += row["outcome"] == "FLAW"
        mark = "as predicted" if row["outcome"] == predicted else "PREDICTION WRONG"
        print(f"{ident:<4} {case.__name__:<28} {row['outcome']:<6} [{mark}]  {row['evidence']}")
    print(f"\n{flaws} of {len(CASES)} cases show a flaw")


if __name__ == "__main__":
    main()
