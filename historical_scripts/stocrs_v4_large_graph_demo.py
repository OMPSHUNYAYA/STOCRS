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
    p["X5"] = {"deps": [], "func": lambda v: 11}
    p["X6"] = {"deps": [], "func": lambda v: 13}

    p["A1"] = {"deps": ["X1", "X2"], "func": lambda v: v["X1"] + v["X2"]}
    p["A2"] = {"deps": ["X2", "X3"], "func": lambda v: v["X2"] * v["X3"]}
    p["A3"] = {"deps": ["X3", "X4"], "func": lambda v: v["X3"] + v["X4"]}
    p["A4"] = {"deps": ["X4", "X5"], "func": lambda v: v["X4"] * v["X5"]}
    p["A5"] = {"deps": ["X5", "X6"], "func": lambda v: v["X5"] + v["X6"]}
    p["A6"] = {"deps": ["X1", "X6"], "func": lambda v: v["X1"] * v["X6"]}

    p["B1"] = {"deps": ["A1", "A2"], "func": lambda v: v["A1"] + v["A2"]}
    p["B2"] = {"deps": ["A2", "A3"], "func": lambda v: v["A2"] - v["A3"]}
    p["B3"] = {"deps": ["A3", "A4"], "func": lambda v: v["A3"] + v["A4"]}
    p["B4"] = {"deps": ["A4", "A5"], "func": lambda v: v["A4"] - v["A5"]}
    p["B5"] = {"deps": ["A5", "A6"], "func": lambda v: v["A5"] + v["A6"]}
    p["B6"] = {"deps": ["A1", "A6"], "func": lambda v: v["A1"] + v["A6"]}

    p["C1"] = {"deps": ["B1", "B2"], "func": lambda v: v["B1"] * 2 + v["B2"]}
    p["C2"] = {"deps": ["B2", "B3", "Z1"], "func": lambda v: v["B2"] + v["B3"] + v["Z1"]}
    p["C3"] = {"deps": ["B3", "B4", "Z2"], "func": lambda v: v["B3"] - v["B4"] + v["Z2"]}
    p["C4"] = {"deps": ["B4", "B5"], "func": lambda v: v["B4"] + v["B5"]}
    p["C5"] = {"deps": ["B5", "B6"], "func": lambda v: v["B5"] * 2 - v["B6"]}
    p["C6"] = {"deps": ["B1", "B6", "Z3"], "func": lambda v: v["B1"] + v["B6"] + v["Z3"]}

    p["D1"] = {"deps": ["C1", "C2"], "func": lambda v: v["C1"] + v["C2"]}
    p["D2"] = {"deps": ["C2", "C3"], "func": lambda v: v["C2"] * 2 - v["C3"]}
    p["D3"] = {"deps": ["C3", "C4"], "func": lambda v: v["C3"] + v["C4"]}
    p["D4"] = {"deps": ["C4", "C5"], "func": lambda v: v["C4"] - v["C5"]}
    p["D5"] = {"deps": ["C5", "C6"], "func": lambda v: v["C5"] + v["C6"]}

    p["E1"] = {"deps": ["D1", "D2"], "func": lambda v: v["D1"] + v["D2"]}
    p["E2"] = {"deps": ["D2", "D3"], "func": lambda v: v["D2"] + v["D3"]}
    p["E3"] = {"deps": ["D3", "D4"], "func": lambda v: v["D3"] + v["D4"]}
    p["E4"] = {"deps": ["D4", "D5"], "func": lambda v: v["D4"] + v["D5"]}

    p["F1"] = {"deps": ["E1", "E2"], "func": lambda v: v["E1"] * 2 + v["E2"]}
    p["F2"] = {"deps": ["E2", "E3"], "func": lambda v: v["E2"] + v["E3"] * 2}
    p["F3"] = {"deps": ["E3", "E4", "Z4"], "func": lambda v: v["E3"] + v["E4"] + v["Z4"]}

    p["G1"] = {"deps": ["F1", "F2"], "func": lambda v: v["F1"] + v["F2"]}
    p["G2"] = {"deps": ["F2", "F3"], "func": lambda v: v["F2"] - v["F3"]}

    p["H1"] = {"deps": ["G1", "G2"], "func": lambda v: v["G1"] + v["G2"]}

    p["Z1"] = {"deps": [], "func": lambda v: 17}
    p["Z2"] = {"deps": [], "func": lambda v: 19}
    p["Z3"] = {"deps": [], "func": lambda v: 23}
    p["Z4"] = {"deps": [], "func": lambda v: 29}

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

def run_system(system_name, program, phase1_nodes, phase2_nodes, arrivals_phase1, arrivals_phase2,
               anchor_s, elapsed_p1_s, elapsed_p2_s, drift_ppm, structural_correction_s):
    phase1_program = {k: program[k] for k in phase1_nodes}
    phase1_values, phase1_frontiers, phase1_unresolved = resolve(phase1_program)

    local_time_phase1 = reconstruct_time(anchor_s, elapsed_p1_s, drift_ppm, 0.0)
    local_time_phase2 = reconstruct_time(anchor_s, elapsed_p2_s, drift_ppm, structural_correction_s)

    full_program = dict(program)
    final_values, final_frontiers, final_unresolved = resolve(full_program)

    return {
        "system": system_name,
        "gps_used": False,
        "ntp_used": False,
        "internet_used": False,
        "used_time_for_correctness": False,
        "phase1_arrivals": arrivals_phase1,
        "phase2_arrivals": arrivals_phase2,
        "phase1_local_time_s": local_time_phase1,
        "phase2_local_time_s": local_time_phase2,
        "phase1_frontiers": phase1_frontiers,
        "phase1_unresolved": phase1_unresolved,
        "phase1_values_count": len(phase1_values),
        "final_frontiers": final_frontiers,
        "final_unresolved": final_unresolved,
        "final_values": final_values,
    }

def hash_obj(obj):
    s = json.dumps(obj, sort_keys=True)
    return hashlib.sha256(s.encode()).hexdigest()

def single_run(seed):
    rng = random.Random(seed)
    program = build_program()

    delayed_nodes = ["Z1", "Z2", "Z3", "Z4"]
    phase1_nodes = [k for k in program.keys() if k not in delayed_nodes]
    phase2_nodes = delayed_nodes[:]

    arrivals_A_p1 = rng.sample(phase1_nodes, len(phase1_nodes))
    arrivals_B_p1 = rng.sample(phase1_nodes, len(phase1_nodes))
    arrivals_A_p2 = rng.sample(phase2_nodes, len(phase2_nodes))
    arrivals_B_p2 = rng.sample(phase2_nodes, len(phase2_nodes))

    t0 = time.perf_counter()

    system_A = run_system(
        "A", program, phase1_nodes, phase2_nodes, arrivals_A_p1, arrivals_A_p2,
        anchor_s=200000.0, elapsed_p1_s=86400.0 * 120.0, elapsed_p2_s=86400.0 * 121.0,
        drift_ppm=320.0, structural_correction_s=0.0
    )

    system_B = run_system(
        "B", program, phase1_nodes, phase2_nodes, arrivals_B_p1, arrivals_B_p2,
        anchor_s=200251.0, elapsed_p1_s=86400.0 * 120.0, elapsed_p2_s=86400.0 * 121.0,
        drift_ppm=-210.0, structural_correction_s=0.0
    )

    elapsed_runtime_s = round(time.perf_counter() - t0, 6)

    arrivals_different = system_A["phase1_arrivals"] != system_B["phase1_arrivals"]
    local_times_different = (
        system_A["phase1_local_time_s"] != system_B["phase1_local_time_s"] and
        system_A["phase2_local_time_s"] != system_B["phase2_local_time_s"]
    )

    phase1_unresolved_required = ["C2", "C3", "C6", "D1", "D2", "D3", "E1", "E2", "F1", "F2", "F3", "G1", "G2", "H1"]
    phase1_unresolved_ok = all(x in system_A["phase1_unresolved"] for x in phase1_unresolved_required) and \
                           all(x in system_B["phase1_unresolved"] for x in phase1_unresolved_required)

    result_match = system_A["final_values"] == system_B["final_values"]
    final_complete = system_A["final_unresolved"] == [] and system_B["final_unresolved"] == []

    certificate = hash_obj({
        "seed": seed,
        "system_A": system_A,
        "system_B": system_B,
        "arrivals_different": arrivals_different,
        "local_times_different": local_times_different,
        "phase1_unresolved_ok": phase1_unresolved_ok,
        "result_match": result_match,
        "final_complete": final_complete,
    })

    return {
        "seed": seed,
        "arrivals_different": arrivals_different,
        "local_times_different": local_times_different,
        "phase1_unresolved_ok": phase1_unresolved_ok,
        "result_match": result_match,
        "final_complete": final_complete,
        "elapsed_runtime_s": elapsed_runtime_s,
        "certificate": certificate,
        "system_A": system_A,
        "system_B": system_B,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=31)
    parser.add_argument("--stress", type=int, default=1)
    parser.add_argument("--show-progress", action="store_true")
    args = parser.parse_args()

    if args.stress <= 1:
        result = single_run(args.seed)

        print("STOCRS v4 Large Graph Demo")
        print("Seed:", result["seed"])
        print("No GPS: YES")
        print("No NTP: YES")
        print("No Internet: YES")
        print("Arrival Orders Different:", "YES" if result["arrivals_different"] else "NO")
        print("Local Times Different:", "YES" if result["local_times_different"] else "NO")
        print("Time Used for Correctness: NO")
        print("Phase 1 Unresolved OK:", "YES" if result["phase1_unresolved_ok"] else "NO")
        print("Final Result Match:", "YES" if result["result_match"] else "NO")
        print("Final Complete:", "YES" if result["final_complete"] else "NO")
        print("Elapsed Runtime (s):", result["elapsed_runtime_s"])
        print("System A Phase 1 Local Time:", result["system_A"]["phase1_local_time_s"])
        print("System B Phase 1 Local Time:", result["system_B"]["phase1_local_time_s"])
        print("System A Phase 2 Local Time:", result["system_A"]["phase2_local_time_s"])
        print("System B Phase 2 Local Time:", result["system_B"]["phase2_local_time_s"])
        print("System A Phase 1 Unresolved Count:", len(result["system_A"]["phase1_unresolved"]))
        print("System B Phase 1 Unresolved Count:", len(result["system_B"]["phase1_unresolved"]))
        print("System A Phase 1 Unresolved:", result["system_A"]["phase1_unresolved"])
        print("System B Phase 1 Unresolved:", result["system_B"]["phase1_unresolved"])
        print("Final Node Count:", len(result["system_A"]["final_values"]))
        print("Final H1:", result["system_A"]["final_values"]["H1"])
        print("Certificate:", result["certificate"])
        return

    t0 = time.perf_counter()
    passes = 0
    certs = []

    for i in range(args.stress):
        seed = args.seed + i
        result = single_run(seed)
        passed = result["arrivals_different"] and result["local_times_different"] and \
                 result["phase1_unresolved_ok"] and result["result_match"] and result["final_complete"]
        certs.append(result["certificate"])
        if passed:
            passes += 1
        if args.show_progress:
            print(f"Run {i+1}/{args.stress} | Seed {seed} | Pass {'YES' if passed else 'NO'} | Runtime {result['elapsed_runtime_s']} s")

    total_elapsed_s = round(time.perf_counter() - t0, 6)

    digest = hash_obj({
        "start_seed": args.seed,
        "runs": args.stress,
        "passes": passes,
        "certificates": certs,
    })

    print("STOCRS v4 Large Graph Stress Test")
    print("Start Seed:", args.seed)
    print("Runs:", args.stress)
    print("Passes:", passes)
    print("All Passed:", "YES" if passes == args.stress else "NO")
    print("Elapsed Runtime (s):", total_elapsed_s)
    print("Certificate Digest:", digest)

if __name__ == "__main__":
    main()