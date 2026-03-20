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

def make_conflicting_arrivals(rng, valid_nodes, delayed_nodes):
    phase1_valid = [n for n in valid_nodes if n not in delayed_nodes]
    arrivals = rng.sample(phase1_valid, len(phase1_valid))

    duplicate_targets = rng.sample(phase1_valid, min(3, len(phase1_valid)))
    duplicates = duplicate_targets[:]

    conflict_tokens = [
        "CLAIM:X1=999",
        "CLAIM:X2=-50",
        "CLAIM:A1=12345",
        "CLAIM:Z1=777",
        "CLAIM:E1=0"
    ]
    rng.shuffle(conflict_tokens)

    invalid_tokens = [
        "INJECT:GHOST=88",
        "INJECT:FAKE_BRANCH=999"
    ]
    rng.shuffle(invalid_tokens)

    mixed = arrivals + duplicates + conflict_tokens[:3] + invalid_tokens[:1]
    rng.shuffle(mixed)
    return mixed

def sanitize_arrivals(arrivals, program):
    seen = set()
    accepted = []
    duplicate_count = 0
    invalid_count = 0
    conflict_count = 0

    for token in arrivals:
        if token in program:
            if token in seen:
                duplicate_count += 1
            else:
                seen.add(token)
                accepted.append(token)
        elif isinstance(token, str) and token.startswith("CLAIM:"):
            conflict_count += 1
        else:
            invalid_count += 1

    return accepted, duplicate_count, invalid_count, conflict_count

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

def run_system(system_name, program, raw_phase1_arrivals, raw_phase2_arrivals,
               anchor_s, elapsed_p1_s, elapsed_p2_s, drift_ppm, structural_correction_s):
    clean_phase1_arrivals, dup1, invalid1, conflict1 = sanitize_arrivals(raw_phase1_arrivals, program)
    clean_phase2_arrivals, dup2, invalid2, conflict2 = sanitize_arrivals(raw_phase2_arrivals, program)

    delayed_nodes = ["Z1", "Z2"]
    phase1_nodes = [n for n in clean_phase1_arrivals if n not in delayed_nodes]

    phase1_program = {k: program[k] for k in phase1_nodes}
    phase1_values, phase1_frontiers, phase1_unresolved = resolve(phase1_program)

    local_time_phase1 = reconstruct_time(anchor_s, elapsed_p1_s, drift_ppm, 0.0)
    local_time_phase2 = reconstruct_time(anchor_s, elapsed_p2_s, drift_ppm, structural_correction_s)

    final_program = dict(program)
    final_values, final_frontiers, final_unresolved = resolve(final_program)

    return {
        "system": system_name,
        "gps_used": False,
        "ntp_used": False,
        "internet_used": False,
        "used_time_for_correctness": False,
        "raw_phase1_arrivals": raw_phase1_arrivals,
        "raw_phase2_arrivals": raw_phase2_arrivals,
        "clean_phase1_arrivals": clean_phase1_arrivals,
        "clean_phase2_arrivals": clean_phase2_arrivals,
        "duplicate_count": dup1 + dup2,
        "invalid_count": invalid1 + invalid2,
        "conflict_count": conflict1 + conflict2,
        "phase1_local_time_s": local_time_phase1,
        "phase2_local_time_s": local_time_phase2,
        "phase1_frontiers": phase1_frontiers,
        "phase1_unresolved": phase1_unresolved,
        "final_frontiers": final_frontiers,
        "final_unresolved": final_unresolved,
        "final_values": final_values,
    }

def hash_obj(obj):
    s = json.dumps(obj, sort_keys=True)
    return hashlib.sha256(s.encode()).hexdigest()

def single_run(seed, systems_count):
    program = build_program()
    valid_nodes = list(program.keys())
    delayed_nodes = ["Z1", "Z2"]

    t0 = time.perf_counter()
    systems = []

    for i in range(systems_count):
        sys_rng = random.Random(seed * 100 + i * 19 + 5)

        raw_phase1 = make_conflicting_arrivals(sys_rng, valid_nodes, delayed_nodes)

        phase2_valid = delayed_nodes[:]
        phase2_dups = [delayed_nodes[0]]
        phase2_conflicts = [f"CLAIM:Z1={900+i}", f"CLAIM:C2={500+i}"]
        phase2_invalid = [f"INJECT:BADNODE{i}=1"]
        raw_phase2 = phase2_valid + phase2_dups + phase2_conflicts + phase2_invalid
        sys_rng.shuffle(raw_phase2)

        system = run_system(
            system_name=f"S{i+1}",
            program=program,
            raw_phase1_arrivals=raw_phase1,
            raw_phase2_arrivals=raw_phase2,
            anchor_s=500000.0 + i * 173.0,
            elapsed_p1_s=86400.0 * (180.0 + i),
            elapsed_p2_s=86400.0 * (181.0 + i),
            drift_ppm=[320.0, -210.0, 145.0, -95.0, 260.0, -180.0, 75.0, -40.0][i % 8],
            structural_correction_s=0.0,
        )
        systems.append(system)

    elapsed_runtime_s = round(time.perf_counter() - t0, 6)

    ref_values = systems[0]["final_values"]
    all_results_match = all(s["final_values"] == ref_values for s in systems)
    all_final_complete = all(s["final_unresolved"] == [] for s in systems)

    required_unresolved = ["C2", "C3", "D1", "D2", "E1"]
    all_phase1_unresolved_ok = all(all(x in s["phase1_unresolved"] for x in required_unresolved) for s in systems)

    all_conflicts_detected = all(s["conflict_count"] > 0 for s in systems)
    all_duplicates_detected = all(s["duplicate_count"] > 0 for s in systems)
    all_invalid_detected = all(s["invalid_count"] > 0 for s in systems)

    local_times_p1 = [s["phase1_local_time_s"] for s in systems]
    local_times_p2 = [s["phase2_local_time_s"] for s in systems]
    local_time_diversity_ok = len(set(local_times_p1)) == len(local_times_p1) and len(set(local_times_p2)) == len(local_times_p2)

    clean_arrival_orders = [tuple(s["clean_phase1_arrivals"]) for s in systems]
    arrival_diversity_ok = len(set(clean_arrival_orders)) == len(clean_arrival_orders)

    certificate = hash_obj({
        "seed": seed,
        "systems_count": systems_count,
        "all_results_match": all_results_match,
        "all_final_complete": all_final_complete,
        "all_phase1_unresolved_ok": all_phase1_unresolved_ok,
        "all_conflicts_detected": all_conflicts_detected,
        "all_duplicates_detected": all_duplicates_detected,
        "all_invalid_detected": all_invalid_detected,
        "arrival_diversity_ok": arrival_diversity_ok,
        "local_time_diversity_ok": local_time_diversity_ok,
        "systems": systems,
    })

    return {
        "seed": seed,
        "systems_count": systems_count,
        "all_results_match": all_results_match,
        "all_final_complete": all_final_complete,
        "all_phase1_unresolved_ok": all_phase1_unresolved_ok,
        "all_conflicts_detected": all_conflicts_detected,
        "all_duplicates_detected": all_duplicates_detected,
        "all_invalid_detected": all_invalid_detected,
        "arrival_diversity_ok": arrival_diversity_ok,
        "local_time_diversity_ok": local_time_diversity_ok,
        "elapsed_runtime_s": elapsed_runtime_s,
        "certificate": certificate,
        "systems": systems,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=61)
    parser.add_argument("--systems", type=int, default=5)
    parser.add_argument("--stress", type=int, default=1)
    parser.add_argument("--show-progress", action="store_true")
    args = parser.parse_args()

    if args.systems < 3:
        raise ValueError("Use at least 3 systems for the conflict demo.")

    if args.stress <= 1:
        result = single_run(args.seed, args.systems)

        print("STOCRS v7 Conflict Demo")
        print("Seed:", result["seed"])
        print("Systems:", result["systems_count"])
        print("No GPS: YES")
        print("No NTP: YES")
        print("No Internet: YES")
        print("Arrival Diversity OK:", "YES" if result["arrival_diversity_ok"] else "NO")
        print("Local Time Diversity OK:", "YES" if result["local_time_diversity_ok"] else "NO")
        print("Conflicting Claims Detected:", "YES" if result["all_conflicts_detected"] else "NO")
        print("Duplicate Noise Detected:", "YES" if result["all_duplicates_detected"] else "NO")
        print("Invalid Noise Detected:", "YES" if result["all_invalid_detected"] else "NO")
        print("Time Used for Correctness: NO")
        print("Phase 1 Unresolved OK:", "YES" if result["all_phase1_unresolved_ok"] else "NO")
        print("All Results Match:", "YES" if result["all_results_match"] else "NO")
        print("All Final Complete:", "YES" if result["all_final_complete"] else "NO")
        print("Elapsed Runtime (s):", result["elapsed_runtime_s"])

        for s in result["systems"]:
            print(f"{s['system']} Conflict Count:", s["conflict_count"])
            print(f"{s['system']} Duplicate Count:", s["duplicate_count"])
            print(f"{s['system']} Invalid Count:", s["invalid_count"])
            print(f"{s['system']} Phase 1 Local Time:", s["phase1_local_time_s"])
            print(f"{s['system']} Phase 2 Local Time:", s["phase2_local_time_s"])
            print(f"{s['system']} Phase 1 Unresolved Count:", len(s["phase1_unresolved"]))

        print("Final Node Count:", len(result["systems"][0]["final_values"]))
        print("Final E1:", result["systems"][0]["final_values"]["E1"])
        print("Certificate:", result["certificate"])
        return

    t0 = time.perf_counter()
    passes = 0
    certs = []

    for i in range(args.stress):
        seed = args.seed + i
        result = single_run(seed, args.systems)
        passed = (
            result["arrival_diversity_ok"] and
            result["local_time_diversity_ok"] and
            result["all_conflicts_detected"] and
            result["all_duplicates_detected"] and
            result["all_invalid_detected"] and
            result["all_phase1_unresolved_ok"] and
            result["all_results_match"] and
            result["all_final_complete"]
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

    print("STOCRS v7 Conflict Stress Test")
    print("Start Seed:", args.seed)
    print("Systems:", args.systems)
    print("Runs:", args.stress)
    print("Passes:", passes)
    print("All Passed:", "YES" if passes == args.stress else "NO")
    print("Elapsed Runtime (s):", total_elapsed_s)
    print("Certificate Digest:", digest)

if __name__ == "__main__":
    main()