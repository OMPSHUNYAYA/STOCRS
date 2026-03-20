import os
import sys
import random
import argparse
import json
import time

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from runtime.stocrs_engine_v1 import (
    build_program,
    initial_fragment_for_system,
    bounded_union,
    run_system,
    hash_obj,
)


def build_conflict_story(program):
    stable_run = run_system(
        system_name="S1",
        program=program,
        known_nodes=["X1", "X2", "A1"],
        anchor_s=1000.0,
        elapsed_s=60.0,
        drift_ppm=0.0,
        claims={"X1": [2, 2], "X2": [3, 3]},
    )

    conflict_run = run_system(
        system_name="S1",
        program=program,
        known_nodes=["X1", "X2", "A1"],
        anchor_s=1000.0,
        elapsed_s=60.0,
        drift_ppm=0.0,
        claims={"X1": [2, 9], "X2": [3, 3]},
    )

    recovery_run = run_system(
        system_name="S1",
        program=program,
        known_nodes=["X1", "X2", "A1"],
        anchor_s=1000.0,
        elapsed_s=60.0,
        drift_ppm=0.0,
        claims={"X1": [2, 2, 9], "X2": [3, 3]},
    )

    stable_ok = (
        stable_run["values"].get("X1") == 2
        and stable_run["values"].get("X2") == 3
        and stable_run["values"].get("A1") == 5
        and len(stable_run["conflicts"]) == 0
        and len(stable_run["unresolved"]) == 0
    )

    conflict_ok = (
        conflict_run["values"].get("X2") == 3
        and "X1" in conflict_run["conflicts"]
        and "A1" in conflict_run["unresolved"]
        and "A1" not in conflict_run["values"]
    )

    recovery_ok = (
        recovery_run["values"].get("X1") == 2
        and recovery_run["values"].get("X2") == 3
        and recovery_run["values"].get("A1") == 5
        and len(recovery_run["conflicts"]) == 0
        and len(recovery_run["unresolved"]) == 0
    )

    story = {
        "stable_run": stable_run,
        "conflict_run": conflict_run,
        "recovery_run": recovery_run,
        "stable_ok": stable_ok,
        "conflict_ok": conflict_ok,
        "recovery_ok": recovery_ok,
    }
    story["certificate"] = hash_obj(story)
    return story


def build_demo(seed, systems_count):
    rng = random.Random(seed)
    program = build_program()
    full_nodes = list(program.keys())
    drift_list = [320.0, -210.0, 145.0, -95.0, 260.0, -180.0, 75.0, -40.0]

    t0 = time.perf_counter()

    phase1 = []
    for i in range(systems_count):
        frag = initial_fragment_for_system(i)
        rng.shuffle(frag)
        phase1.append(
            run_system(
                f"S{i+1}",
                program,
                known_nodes=frag,
                anchor_s=800000.0 + i * 157.0,
                elapsed_s=86400.0 * (240.0 + i),
                drift_ppm=drift_list[i % len(drift_list)],
            )
        )

    phase2 = []
    for i in range(systems_count):
        a = phase1[i]["known_nodes"]
        b = phase1[(i + 1) % systems_count]["known_nodes"]
        shared = bounded_union(a, b, cap=7)
        phase2.append(
            run_system(
                f"S{i+1}",
                program,
                known_nodes=shared,
                anchor_s=800000.0 + i * 157.0,
                elapsed_s=86400.0 * (241.0 + i),
                drift_ppm=drift_list[i % len(drift_list)],
            )
        )

    phase3 = []
    for i in range(systems_count):
        a = phase2[i]["known_nodes"]
        b = phase2[(i + 2) % systems_count]["known_nodes"]
        shared = bounded_union(a, b, cap=10)
        phase3.append(
            run_system(
                f"S{i+1}",
                program,
                known_nodes=shared,
                anchor_s=800000.0 + i * 157.0,
                elapsed_s=86400.0 * (242.0 + i),
                drift_ppm=drift_list[i % len(drift_list)],
            )
        )

    phase4 = []
    for i in range(systems_count):
        a = phase3[i]["known_nodes"]
        b = phase3[(i + 3) % systems_count]["known_nodes"]
        shared = bounded_union(a, b, cap=14)
        phase4.append(
            run_system(
                f"S{i+1}",
                program,
                known_nodes=shared,
                anchor_s=800000.0 + i * 157.0,
                elapsed_s=86400.0 * (243.0 + i),
                drift_ppm=drift_list[i % len(drift_list)],
            )
        )

    phase5 = []
    for i in range(systems_count):
        full_known = full_nodes[:]
        rng.shuffle(full_known)
        phase5.append(
            run_system(
                f"S{i+1}",
                program,
                known_nodes=full_known,
                anchor_s=800000.0 + i * 157.0,
                elapsed_s=86400.0 * (244.0 + i),
                drift_ppm=drift_list[i % len(drift_list)],
            )
        )

    conflict_story = build_conflict_story(program)

    elapsed_runtime_s = round(time.perf_counter() - t0, 6)

    phase1_diversity_ok = len(set(tuple(s["known_nodes"]) for s in phase1)) == len(phase1)
    phase1_incomplete_ok = all(len(s["known_nodes"]) < len(full_nodes) for s in phase1)

    phase2_bounded_ok = all(s["known_count"] <= 7 for s in phase2)
    phase3_bounded_ok = all(s["known_count"] <= 10 for s in phase3)
    phase4_bounded_ok = all(s["known_count"] <= 14 for s in phase4)

    phase1_unresolved_exists = all(len(s["unresolved"]) > 0 for s in phase1)
    phase2_unresolved_exists = all(len(s["unresolved"]) > 0 for s in phase2)
    phase3_unresolved_exists = all(len(s["unresolved"]) > 0 for s in phase3)
    phase4_unresolved_exists = all(len(s["unresolved"]) > 0 for s in phase4)

    final_complete_ok = all(len(s["unresolved"]) == 0 for s in phase5)
    final_match_ok = len(set(hash_obj(s["values"]) for s in phase5)) == 1
    final_node_count = len(phase5[0]["values"]) if phase5 else 0
    final_e1_values = [s["values"].get("E1") for s in phase5]
    final_e1 = final_e1_values[0] if final_e1_values else None

    certificate_payload = {
        "name": "STOCRS Canonical Demo",
        "seed": seed,
        "systems": systems_count,
        "no_gps": True,
        "no_ntp": True,
        "no_internet": True,
        "time_used_for_correctness": False,
        "phase1_diversity_ok": phase1_diversity_ok,
        "phase1_incomplete_ok": phase1_incomplete_ok,
        "phase2_bounded_ok": phase2_bounded_ok,
        "phase3_bounded_ok": phase3_bounded_ok,
        "phase4_bounded_ok": phase4_bounded_ok,
        "phase1_unresolved_exists": phase1_unresolved_exists,
        "phase2_unresolved_exists": phase2_unresolved_exists,
        "phase3_unresolved_exists": phase3_unresolved_exists,
        "phase4_unresolved_exists": phase4_unresolved_exists,
        "final_complete_ok": final_complete_ok,
        "final_match_ok": final_match_ok,
        "final_node_count": final_node_count,
        "final_e1": final_e1,
        "conflict_story": {
            "stable_ok": conflict_story["stable_ok"],
            "conflict_ok": conflict_story["conflict_ok"],
            "recovery_ok": conflict_story["recovery_ok"],
            "certificate": conflict_story["certificate"],
        },
        "phase1": phase1,
        "phase2": phase2,
        "phase3": phase3,
        "phase4": phase4,
        "phase5": phase5,
    }

    result = dict(certificate_payload)
    result["conflict_story_detail"] = conflict_story
    result["elapsed_runtime_s"] = elapsed_runtime_s
    result["certificate"] = hash_obj(certificate_payload)
    return result


def print_demo(result):
    print("STOCRS Canonical Demo")
    print()
    print(f"Seed: {result['seed']}")
    print(f"Systems: {result['systems']}")
    print()
    print(f"No GPS: {'YES' if result['no_gps'] else 'NO'}")
    print(f"No NTP: {'YES' if result['no_ntp'] else 'NO'}")
    print(f"No Internet: {'YES' if result['no_internet'] else 'NO'}")
    print(f"Time Used for Correctness: {'YES' if result['time_used_for_correctness'] else 'NO'}")
    print()
    print(f"Phase 1 Diversity OK: {'YES' if result['phase1_diversity_ok'] else 'NO'}")
    print(f"Phase 1 Incomplete OK: {'YES' if result['phase1_incomplete_ok'] else 'NO'}")
    print(f"Phase 2 Bounded OK: {'YES' if result['phase2_bounded_ok'] else 'NO'}")
    print(f"Phase 3 Bounded OK: {'YES' if result['phase3_bounded_ok'] else 'NO'}")
    print(f"Phase 4 Bounded OK: {'YES' if result['phase4_bounded_ok'] else 'NO'}")
    print()
    print(f"Phase 1 Unresolved Exists: {'YES' if result['phase1_unresolved_exists'] else 'NO'}")
    print(f"Phase 2 Unresolved Exists: {'YES' if result['phase2_unresolved_exists'] else 'NO'}")
    print(f"Phase 3 Unresolved Exists: {'YES' if result['phase3_unresolved_exists'] else 'NO'}")
    print(f"Phase 4 Unresolved Exists: {'YES' if result['phase4_unresolved_exists'] else 'NO'}")
    print()
    print(f"Final Complete OK: {'YES' if result['final_complete_ok'] else 'NO'}")
    print(f"Final Match OK: {'YES' if result['final_match_ok'] else 'NO'}")
    print(f"Final Node Count: {result['final_node_count']}")
    print(f"Final E1: {result['final_e1']}")
    print()
    print("Conflict Story")
    print(f"Stable OK: {'YES' if result['conflict_story']['stable_ok'] else 'NO'}")
    print(f"Conflict OK: {'YES' if result['conflict_story']['conflict_ok'] else 'NO'}")
    print(f"Recovery OK: {'YES' if result['conflict_story']['recovery_ok'] else 'NO'}")
    print(f"Conflict Story Certificate: {result['conflict_story']['certificate']}")
    print()
    print(f"Elapsed Runtime: {result['elapsed_runtime_s']} s")
    print(f"Certificate: {result['certificate']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=101)
    parser.add_argument("--systems", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = build_demo(seed=args.seed, systems_count=args.systems)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_demo(result)


if __name__ == "__main__":
    main()