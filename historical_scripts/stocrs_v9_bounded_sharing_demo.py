import random
import hashlib
import argparse
import json
import time

def build_program():
    p = {}

    p["X1"] = {"deps": [], "func": lambda v: 2}
    p["X2"] = {"deps": [], "func": lambda v: 3}
    p["X3"] = {"deps": [], "func": lambda v: 5}
    p["X4"] = {"deps": [], "func": lambda v: 7}

    p["A1"] = {"deps": ["X1", "X2"], "func": lambda v: v["X1"] + v["X2"]}
    p["A2"] = {"deps": ["X2", "X3"], "func": lambda v: v["X2"] * v["X3"]}
    p["A3"] = {"deps": ["X3", "X4"], "func": lambda v: v["X3"] + v["X4"]}
    p["A4"] = {"deps": ["X1", "X4"], "func": lambda v: v["X1"] * v["X4"]}

    p["Z1"] = {"deps": [], "func": lambda v: 17}
    p["Z2"] = {"deps": [], "func": lambda v: 19}

    p["B1"] = {"deps": ["A1", "A2"], "func": lambda v: v["A1"] + v["A2"]}
    p["B2"] = {"deps": ["A2", "A3"], "func": lambda v: v["A2"] - v["A3"]}
    p["B3"] = {"deps": ["A3", "A4"], "func": lambda v: v["A3"] + v["A4"]}
    p["B4"] = {"deps": ["A1", "A4"], "func": lambda v: v["A1"] + v["A4"]}

    p["C1"] = {"deps": ["B1", "B2"], "func": lambda v: v["B1"] + v["B2"]}
    p["C2"] = {"deps": ["B2", "B3", "Z1"], "func": lambda v: v["B2"] + v["B3"] + v["Z1"]}
    p["C3"] = {"deps": ["B3", "B4", "Z2"], "func": lambda v: v["B3"] + v["B4"] + v["Z2"]}

    p["D1"] = {"deps": ["C1", "C2"], "func": lambda v: v["C1"] * 2 + v["C2"]}
    p["D2"] = {"deps": ["C2", "C3"], "func": lambda v: v["C2"] + v["C3"]}

    p["E1"] = {"deps": ["D1", "D2"], "func": lambda v: v["D1"] + v["D2"]}

    return p

def reconstruct_time(anchor_s, elapsed_s, drift_ppm, structural_correction_s):
    return round(anchor_s + elapsed_s * (1.0 + drift_ppm / 1000000.0) + structural_correction_s, 6)

def resolve(program_subset):
    values = {}
    resolved = set()
    unresolved = set(program_subset.keys())
    frontiers = []

    while True:
        ready = []
        for node in unresolved:
            deps = program_subset[node]["deps"]
            if all(d in resolved for d in deps):
                ready.append(node)

        if not ready:
            break

        frontier = sorted(ready)
        for node in frontier:
            values[node] = program_subset[node]["func"](values)
            resolved.add(node)
            unresolved.remove(node)

        frontiers.append(frontier)

    return values, frontiers, sorted(unresolved)

def initial_fragment_for_system(index):
    # Intentionally incomplete and downstream-heavy
    fragments = [
        ["X1", "A1", "B1", "C1", "D1"],
        ["X2", "A2", "B2", "C2", "D2"],
        ["X3", "A3", "B3", "C3", "E1"],
        ["X4", "A4", "B4", "C3", "D2"],
        ["Z1", "Z2", "B2", "B3", "C2"],
        ["A1", "A2", "C1", "D1", "E1"],
    ]
    return fragments[index % len(fragments)]

def bounded_union(current_nodes, incoming_nodes, cap):
    merged = []
    seen = set()
    for node in current_nodes + incoming_nodes:
        if node not in seen:
            seen.add(node)
            merged.append(node)
        if len(merged) >= cap:
            break
    return merged

def run_system(system_name, program, known_nodes, anchor_s, elapsed_s, drift_ppm):
    program_subset = {k: program[k] for k in known_nodes if k in program}
    values, frontiers, unresolved = resolve(program_subset)
    local_time_s = reconstruct_time(anchor_s, elapsed_s, drift_ppm, 0.0)
    return {
        "system": system_name,
        "known_nodes": known_nodes,
        "known_count": len(known_nodes),
        "local_time_s": local_time_s,
        "frontiers": frontiers,
        "unresolved": unresolved,
        "values": values,
    }

def hash_obj(obj):
    s = json.dumps(obj, sort_keys=True)
    return hashlib.sha256(s.encode()).hexdigest()

def single_run(seed, systems_count):
    rng = random.Random(seed)
    program = build_program()
    full_nodes = list(program.keys())
    drift_list = [320.0, -210.0, 145.0, -95.0, 260.0, -180.0, 75.0, -40.0]

    t0 = time.perf_counter()

    # Phase 1: different incomplete fragments
    phase1 = []
    for i in range(systems_count):
        frag = initial_fragment_for_system(i)[:]
        rng.shuffle(frag)
        phase1.append(
            run_system(
                f"S{i+1}",
                program,
                known_nodes=frag,
                anchor_s=700000.0 + i * 157.0,
                elapsed_s=86400.0 * (220.0 + i),
                drift_ppm=drift_list[i % len(drift_list)],
            )
        )

    # Phase 2: very tight cap, should still stay unresolved
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
                anchor_s=700000.0 + i * 157.0,
                elapsed_s=86400.0 * (221.0 + i),
                drift_ppm=drift_list[i % len(drift_list)],
            )
        )

    # Phase 3: still bounded, but larger
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
                anchor_s=700000.0 + i * 157.0,
                elapsed_s=86400.0 * (222.0 + i),
                drift_ppm=drift_list[i % len(drift_list)],
            )
        )

    # Phase 4: still incomplete but broader
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
                anchor_s=700000.0 + i * 157.0,
                elapsed_s=86400.0 * (223.0 + i),
                drift_ppm=drift_list[i % len(drift_list)],
            )
        )

    # Phase 5: final completion
    phase5 = []
    for i in range(systems_count):
        full_known = full_nodes[:]
        rng.shuffle(full_known)
        phase5.append(
            run_system(
                f"S{i+1}",
                program,
                known_nodes=full_known,
                anchor_s=700000.0 + i * 157.0,
                elapsed_s=86400.0 * (224.0 + i),
                drift_ppm=drift_list[i % len(drift_list)],
            )
        )

    elapsed_runtime_s = round(time.perf_counter() - t0, 6)

    phase1_diversity_ok = len(set(tuple(s["known_nodes"]) for s in phase1)) == len(phase1)
    phase1_incomplete_ok = all(len(s["known_nodes"]) < len(full_nodes) for s in phase1)

    phase2_bounded_ok = all(s["known_count"] <= 7 for s in phase2)
    phase3_bounded_ok = all(s["known_count"] <= 10 for s in phase3)
    phase4_bounded_ok = all(s["known_count"] <= 14 for s in phase4)

    phase2_growth_ok = all(phase2[i]["known_count"] >= phase1[i]["known_count"] for i in range(systems_count))
    phase3_growth_ok = all(phase3[i]["known_count"] >= phase2[i]["known_count"] for i in range(systems_count))
    phase4_growth_ok = all(phase4[i]["known_count"] >= phase3[i]["known_count"] for i in range(systems_count))

    phase1_unresolved_exists = all(len(s["unresolved"]) > 0 for s in phase1)
    phase2_unresolved_exists = all(len(s["unresolved"]) > 0 for s in phase2)
    phase3_unresolved_exists = all(len(s["unresolved"]) > 0 for s in phase3)
    phase4_unresolved_exists = all(len(s["unresolved"]) > 0 for s in phase4)

    phase5_complete_ok = all(s["unresolved"] == [] for s in phase5)
    ref_values = phase5[0]["values"]
    phase5_match_ok = all(s["values"] == ref_values for s in phase5)

    local_times = [s["local_time_s"] for s in phase5]
    local_time_diversity_ok = len(set(local_times)) == len(local_times)

    certificate = hash_obj({
        "seed": seed,
        "systems_count": systems_count,
        "phase1_diversity_ok": phase1_diversity_ok,
        "phase1_incomplete_ok": phase1_incomplete_ok,
        "phase2_bounded_ok": phase2_bounded_ok,
        "phase3_bounded_ok": phase3_bounded_ok,
        "phase4_bounded_ok": phase4_bounded_ok,
        "phase2_growth_ok": phase2_growth_ok,
        "phase3_growth_ok": phase3_growth_ok,
        "phase4_growth_ok": phase4_growth_ok,
        "phase1_unresolved_exists": phase1_unresolved_exists,
        "phase2_unresolved_exists": phase2_unresolved_exists,
        "phase3_unresolved_exists": phase3_unresolved_exists,
        "phase4_unresolved_exists": phase4_unresolved_exists,
        "phase5_complete_ok": phase5_complete_ok,
        "phase5_match_ok": phase5_match_ok,
        "local_time_diversity_ok": local_time_diversity_ok,
        "phase1": phase1,
        "phase2": phase2,
        "phase3": phase3,
        "phase4": phase4,
        "phase5": phase5,
    })

    return {
        "seed": seed,
        "systems_count": systems_count,
        "phase1_diversity_ok": phase1_diversity_ok,
        "phase1_incomplete_ok": phase1_incomplete_ok,
        "phase2_bounded_ok": phase2_bounded_ok,
        "phase3_bounded_ok": phase3_bounded_ok,
        "phase4_bounded_ok": phase4_bounded_ok,
        "phase2_growth_ok": phase2_growth_ok,
        "phase3_growth_ok": phase3_growth_ok,
        "phase4_growth_ok": phase4_growth_ok,
        "phase1_unresolved_exists": phase1_unresolved_exists,
        "phase2_unresolved_exists": phase2_unresolved_exists,
        "phase3_unresolved_exists": phase3_unresolved_exists,
        "phase4_unresolved_exists": phase4_unresolved_exists,
        "phase5_complete_ok": phase5_complete_ok,
        "phase5_match_ok": phase5_match_ok,
        "local_time_diversity_ok": local_time_diversity_ok,
        "elapsed_runtime_s": elapsed_runtime_s,
        "certificate": certificate,
        "phase1": phase1,
        "phase2": phase2,
        "phase3": phase3,
        "phase4": phase4,
        "phase5": phase5,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=81)
    parser.add_argument("--systems", type=int, default=5)
    parser.add_argument("--stress", type=int, default=1)
    parser.add_argument("--show-progress", action="store_true")
    args = parser.parse_args()

    if args.systems < 3:
        raise ValueError("Use at least 3 systems for the bounded-sharing demo.")

    if args.stress <= 1:
        result = single_run(args.seed, args.systems)

        print("STOCRS v9 Bounded Sharing Demo")
        print("Seed:", result["seed"])
        print("Systems:", result["systems_count"])
        print("No GPS: YES")
        print("No NTP: YES")
        print("No Internet: YES")
        print("Phase 1 Diversity OK:", "YES" if result["phase1_diversity_ok"] else "NO")
        print("Phase 1 Incomplete OK:", "YES" if result["phase1_incomplete_ok"] else "NO")
        print("Phase 2 Bounded OK:", "YES" if result["phase2_bounded_ok"] else "NO")
        print("Phase 3 Bounded OK:", "YES" if result["phase3_bounded_ok"] else "NO")
        print("Phase 4 Bounded OK:", "YES" if result["phase4_bounded_ok"] else "NO")
        print("Phase 2 Growth OK:", "YES" if result["phase2_growth_ok"] else "NO")
        print("Phase 3 Growth OK:", "YES" if result["phase3_growth_ok"] else "NO")
        print("Phase 4 Growth OK:", "YES" if result["phase4_growth_ok"] else "NO")
        print("Phase 1 Unresolved Exists:", "YES" if result["phase1_unresolved_exists"] else "NO")
        print("Phase 2 Unresolved Exists:", "YES" if result["phase2_unresolved_exists"] else "NO")
        print("Phase 3 Unresolved Exists:", "YES" if result["phase3_unresolved_exists"] else "NO")
        print("Phase 4 Unresolved Exists:", "YES" if result["phase4_unresolved_exists"] else "NO")
        print("Local Time Diversity OK:", "YES" if result["local_time_diversity_ok"] else "NO")
        print("Time Used for Correctness: NO")
        print("Phase 5 Complete OK:", "YES" if result["phase5_complete_ok"] else "NO")
        print("Phase 5 Match OK:", "YES" if result["phase5_match_ok"] else "NO")
        print("Elapsed Runtime (s):", result["elapsed_runtime_s"])

        for i in range(result["systems_count"]):
            s1 = result["phase1"][i]
            s2 = result["phase2"][i]
            s3 = result["phase3"][i]
            s4 = result["phase4"][i]
            s5 = result["phase5"][i]
            print(f"{s1['system']} Phase1 Known:", s1["known_count"])
            print(f"{s1['system']} Phase2 Known:", s2["known_count"])
            print(f"{s1['system']} Phase3 Known:", s3["known_count"])
            print(f"{s1['system']} Phase4 Known:", s4["known_count"])
            print(f"{s1['system']} Phase5 Known:", s5["known_count"])
            print(f"{s1['system']} Phase1 Unresolved:", len(s1["unresolved"]))
            print(f"{s1['system']} Phase2 Unresolved:", len(s2["unresolved"]))
            print(f"{s1['system']} Phase3 Unresolved:", len(s3["unresolved"]))
            print(f"{s1['system']} Phase4 Unresolved:", len(s4["unresolved"]))
            print(f"{s1['system']} Phase5 Local Time:", s5["local_time_s"])

        print("Final Node Count:", len(result["phase5"][0]["values"]))
        print("Final E1:", result["phase5"][0]["values"]["E1"])
        print("Certificate:", result["certificate"])
        return

    t0 = time.perf_counter()
    passes = 0
    certs = []

    for i in range(args.stress):
        seed = args.seed + i
        result = single_run(seed, args.systems)
        passed = (
            result["phase1_diversity_ok"] and
            result["phase1_incomplete_ok"] and
            result["phase2_bounded_ok"] and
            result["phase3_bounded_ok"] and
            result["phase4_bounded_ok"] and
            result["phase2_growth_ok"] and
            result["phase3_growth_ok"] and
            result["phase4_growth_ok"] and
            result["phase1_unresolved_exists"] and
            result["phase2_unresolved_exists"] and
            result["phase3_unresolved_exists"] and
            result["phase4_unresolved_exists"] and
            result["local_time_diversity_ok"] and
            result["phase5_complete_ok"] and
            result["phase5_match_ok"]
        )
        certs.append(result["certificate"])
        if passed:
            passes += 1
        if args.show_progress:
            print(f"Run {i+1}/{args.stress} | Seed {seed} | Systems {args.systems} | Pass {'YES' if passed else 'NO'} | Runtime {result['elapsed_runtime_s']} s")

    total_elapsed_s = round(time.perf_counter() - t0, 6)

    digest = hash_obj({
        "start_seed": args.seed,
        "systems": args.systems,
        "runs": args.stress,
        "passes": passes,
        "certificates": certs,
    })

    print("STOCRS v9 Bounded Sharing Stress Test")
    print("Start Seed:", args.seed)
    print("Systems:", args.systems)
    print("Runs:", args.stress)
    print("Passes:", passes)
    print("All Passed:", "YES" if passes == args.stress else "NO")
    print("Elapsed Runtime (s):", total_elapsed_s)
    print("Certificate Digest:", digest)

if __name__ == "__main__":
    main()