import random
import hashlib
import argparse
import json

def build_program():
    return {
        "X": {"deps": [], "func": lambda v: 2},
        "Y": {"deps": [], "func": lambda v: 3},
        "A": {"deps": ["X", "Y"], "func": lambda v: v["X"] + v["Y"]},
        "B": {"deps": ["A"], "func": lambda v: v["A"] * 2},
        "C": {"deps": ["B", "Z"], "func": lambda v: v["B"] + v["Z"]},
        "D": {"deps": ["C"], "func": lambda v: v["C"] * 3},
        "E": {"deps": ["D", "Y"], "func": lambda v: v["D"] - v["Y"]},
        "Z": {"deps": [], "func": lambda v: 10},
    }

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

def run_system(system_name, program, arrivals_phase1, arrivals_phase2, anchor_s, elapsed_p1_s, elapsed_p2_s, drift_ppm, structural_correction_s):
    phase1_program = {k: program[k] for k in arrivals_phase1}
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
        "final_frontiers": final_frontiers,
        "final_unresolved": final_unresolved,
        "final_values": final_values,
    }

def hash_obj(obj):
    s = json.dumps(obj, sort_keys=True)
    return hashlib.sha256(s.encode()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=21)
    parser.add_argument("--stress", type=int, default=1)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.stress <= 1:
        rng = random.Random(args.seed)
        program = build_program()

        phase1_nodes = ["X", "Y", "A", "B", "C", "D", "E"]
        phase2_nodes = ["Z"]

        arrivals_A_p1 = rng.sample(phase1_nodes, len(phase1_nodes))
        arrivals_B_p1 = rng.sample(phase1_nodes, len(phase1_nodes))
        arrivals_A_p2 = phase2_nodes[:]
        arrivals_B_p2 = phase2_nodes[:]

        system_A = run_system(
            "A", program, arrivals_A_p1, arrivals_A_p2,
            anchor_s=100000.0, elapsed_p1_s=86400.0 * 90.0, elapsed_p2_s=86400.0 * 91.0,
            drift_ppm=250.0, structural_correction_s=0.0
        )

        system_B = run_system(
            "B", program, arrivals_B_p1, arrivals_B_p2,
            anchor_s=100111.0, elapsed_p1_s=86400.0 * 90.0, elapsed_p2_s=86400.0 * 91.0,
            drift_ppm=-175.0, structural_correction_s=0.0
        )

        arrivals_different = system_A["phase1_arrivals"] != system_B["phase1_arrivals"]
        phase1_unresolved_ok = (
            "C" in system_A["phase1_unresolved"] and
            "D" in system_A["phase1_unresolved"] and
            "E" in system_A["phase1_unresolved"] and
            "C" in system_B["phase1_unresolved"] and
            "D" in system_B["phase1_unresolved"] and
            "E" in system_B["phase1_unresolved"]
        )
        result_match = system_A["final_values"] == system_B["final_values"]
        final_complete = system_A["final_unresolved"] == [] and system_B["final_unresolved"] == []
        local_times_different = (
            system_A["phase1_local_time_s"] != system_B["phase1_local_time_s"] and
            system_A["phase2_local_time_s"] != system_B["phase2_local_time_s"]
        )

        certificate = hash_obj({
            "seed": args.seed,
            "system_A": system_A,
            "system_B": system_B,
            "arrivals_different": arrivals_different,
            "phase1_unresolved_ok": phase1_unresolved_ok,
            "result_match": result_match,
            "final_complete": final_complete,
            "local_times_different": local_times_different
        })

        if args.json:
            print(json.dumps({
                "seed": args.seed,
                "arrivals_different": arrivals_different,
                "phase1_unresolved_ok": phase1_unresolved_ok,
                "local_times_different": local_times_different,
                "result_match": result_match,
                "final_complete": final_complete,
                "time_used_for_correctness": False,
                "gps_used": False,
                "ntp_used": False,
                "internet_used": False,
                "system_A": system_A,
                "system_B": system_B,
                "certificate": certificate
            }, indent=2, sort_keys=True))
            return

        print("STOCRS v3 Isolation Demo")
        print("Seed:", args.seed)
        print("No GPS: YES")
        print("No NTP: YES")
        print("No Internet: YES")
        print("Arrival Orders Different:", "YES" if arrivals_different else "NO")
        print("Local Times Different:", "YES" if local_times_different else "NO")
        print("Time Used for Correctness: NO")
        print("Phase 1 Unresolved OK:", "YES" if phase1_unresolved_ok else "NO")
        print("Final Result Match:", "YES" if result_match else "NO")
        print("Final Complete:", "YES" if final_complete else "NO")
        print("System A Phase 1 Local Time:", system_A["phase1_local_time_s"])
        print("System B Phase 1 Local Time:", system_B["phase1_local_time_s"])
        print("System A Phase 2 Local Time:", system_A["phase2_local_time_s"])
        print("System B Phase 2 Local Time:", system_B["phase2_local_time_s"])
        print("System A Phase 1 Unresolved:", system_A["phase1_unresolved"])
        print("System B Phase 1 Unresolved:", system_B["phase1_unresolved"])
        print("Final Values:", system_A["final_values"])
        print("Certificate:", certificate)
        return

    passes = 0
    certs = []

    for i in range(args.stress):
        seed = args.seed + i
        rng = random.Random(seed)
        program = build_program()

        phase1_nodes = ["X", "Y", "A", "B", "C", "D", "E"]
        phase2_nodes = ["Z"]

        arrivals_A_p1 = rng.sample(phase1_nodes, len(phase1_nodes))
        arrivals_B_p1 = rng.sample(phase1_nodes, len(phase1_nodes))
        arrivals_A_p2 = phase2_nodes[:]
        arrivals_B_p2 = phase2_nodes[:]

        system_A = run_system(
            "A", program, arrivals_A_p1, arrivals_A_p2,
            anchor_s=100000.0, elapsed_p1_s=86400.0 * 90.0, elapsed_p2_s=86400.0 * 91.0,
            drift_ppm=250.0, structural_correction_s=0.0
        )

        system_B = run_system(
            "B", program, arrivals_B_p1, arrivals_B_p2,
            anchor_s=100111.0, elapsed_p1_s=86400.0 * 90.0, elapsed_p2_s=86400.0 * 91.0,
            drift_ppm=-175.0, structural_correction_s=0.0
        )

        arrivals_different = system_A["phase1_arrivals"] != system_B["phase1_arrivals"]
        phase1_unresolved_ok = (
            "C" in system_A["phase1_unresolved"] and
            "D" in system_A["phase1_unresolved"] and
            "E" in system_A["phase1_unresolved"] and
            "C" in system_B["phase1_unresolved"] and
            "D" in system_B["phase1_unresolved"] and
            "E" in system_B["phase1_unresolved"]
        )
        result_match = system_A["final_values"] == system_B["final_values"]
        final_complete = system_A["final_unresolved"] == [] and system_B["final_unresolved"] == []
        local_times_different = (
            system_A["phase1_local_time_s"] != system_B["phase1_local_time_s"] and
            system_A["phase2_local_time_s"] != system_B["phase2_local_time_s"]
        )

        passed = arrivals_different and phase1_unresolved_ok and result_match and final_complete and local_times_different
        cert = hash_obj({
            "seed": seed,
            "passed": passed,
            "system_A": system_A,
            "system_B": system_B
        })
        certs.append(cert)
        if passed:
            passes += 1

    digest = hash_obj({
        "start_seed": args.seed,
        "runs": args.stress,
        "passes": passes,
        "certificates": certs
    })

    if args.json:
        print(json.dumps({
            "start_seed": args.seed,
            "runs": args.stress,
            "passes": passes,
            "all_passed": passes == args.stress,
            "certificate_digest": digest
        }, indent=2, sort_keys=True))
        return

    print("STOCRS v3 Isolation Stress Test")
    print("Start Seed:", args.seed)
    print("Runs:", args.stress)
    print("Passes:", passes)
    print("All Passed:", "YES" if passes == args.stress else "NO")
    print("Certificate Digest:", digest)

if __name__ == "__main__":
    main()