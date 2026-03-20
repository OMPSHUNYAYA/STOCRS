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
        "Z": {"deps": [], "func": lambda v: 10},
    }

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

        frontier = []
        for node in sorted(ready):
            values[node] = program_subset[node]["func"](values)
            resolved.add(node)
            frontier.append(node)

        for node in frontier:
            unresolved.remove(node)

        frontiers.append(frontier)

    return values, frontiers, sorted(unresolved)

def run_system(program, arrivals_phase1, arrivals_phase2):
    phase1_program = {k: program[k] for k in arrivals_phase1}
    phase1_values, phase1_frontiers, phase1_unresolved = resolve(phase1_program)

    full_program = dict(program)
    final_values, final_frontiers, final_unresolved = resolve(full_program)

    return {
        "phase1_arrivals": arrivals_phase1,
        "phase2_arrivals": arrivals_phase2,
        "phase1_values": phase1_values,
        "phase1_frontiers": phase1_frontiers,
        "phase1_unresolved": phase1_unresolved,
        "final_values": final_values,
        "final_frontiers": final_frontiers,
        "final_unresolved": final_unresolved,
    }

def hash_obj(obj):
    s = json.dumps(obj, sort_keys=True)
    return hashlib.sha256(s.encode()).hexdigest()

def single_run(seed):
    rng = random.Random(seed)
    program = build_program()

    all_nodes = list(program.keys())
    phase1_nodes = [n for n in all_nodes if n != "Z"]
    phase2_nodes = ["Z"]

    arrivals_A_p1 = rng.sample(phase1_nodes, len(phase1_nodes))
    arrivals_B_p1 = rng.sample(phase1_nodes, len(phase1_nodes))

    arrivals_A_p2 = phase2_nodes[:]
    arrivals_B_p2 = phase2_nodes[:]

    system_A = run_system(program, arrivals_A_p1, arrivals_A_p2)
    system_B = run_system(program, arrivals_B_p1, arrivals_B_p2)

    phase1_unresolved_ok = (
        len(system_A["phase1_unresolved"]) > 0 and
        len(system_B["phase1_unresolved"]) > 0 and
        "C" in system_A["phase1_unresolved"] and
        "D" in system_A["phase1_unresolved"] and
        "C" in system_B["phase1_unresolved"] and
        "D" in system_B["phase1_unresolved"]
    )

    final_match = system_A["final_values"] == system_B["final_values"]
    final_complete = (
        system_A["final_unresolved"] == [] and
        system_B["final_unresolved"] == []
    )

    passed = phase1_unresolved_ok and final_match and final_complete

    certificate = hash_obj({
        "seed": seed,
        "system_A": system_A,
        "system_B": system_B,
        "passed": passed
    })

    return {
        "seed": seed,
        "passed": passed,
        "phase1_unresolved_ok": phase1_unresolved_ok,
        "final_match": final_match,
        "final_complete": final_complete,
        "certificate": certificate,
        "system_A": system_A,
        "system_B": system_B,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=10)
    parser.add_argument("--stress", type=int, default=1)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.stress <= 1:
        result = single_run(args.seed)
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
            return

        print("STOCRS v2 Fragmented Stress Demo")
        print("Seed:", result["seed"])
        print("Phase 1 Unresolved OK:", "YES" if result["phase1_unresolved_ok"] else "NO")
        print("Final Result Match:", "YES" if result["final_match"] else "NO")
        print("Final Complete:", "YES" if result["final_complete"] else "NO")
        print("Overall Pass:", "YES" if result["passed"] else "NO")
        print("System A Phase 1 Unresolved:", result["system_A"]["phase1_unresolved"])
        print("System B Phase 1 Unresolved:", result["system_B"]["phase1_unresolved"])
        print("Final Values:", result["system_A"]["final_values"])
        print("Certificate:", result["certificate"])
        return

    results = []
    passes = 0
    certs = []

    for i in range(args.stress):
        seed = args.seed + i
        result = single_run(seed)
        results.append(result)
        certs.append(result["certificate"])
        if result["passed"]:
            passes += 1

    digest = hash_obj({
        "start_seed": args.seed,
        "runs": args.stress,
        "certificates": certs,
        "passes": passes,
    })

    if args.json:
        print(json.dumps({
            "start_seed": args.seed,
            "runs": args.stress,
            "passes": passes,
            "all_passed": passes == args.stress,
            "certificate_digest": digest,
            "results": results,
        }, indent=2, sort_keys=True))
        return

    print("STOCRS v2 Fragmented Stress Test")
    print("Start Seed:", args.seed)
    print("Runs:", args.stress)
    print("Passes:", passes)
    print("All Passed:", "YES" if passes == args.stress else "NO")
    print("Certificate Digest:", digest)

if __name__ == "__main__":
    main()