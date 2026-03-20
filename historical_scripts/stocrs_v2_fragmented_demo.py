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

def resolve(program, arrivals):
    values = {}
    resolved = set()
    unresolved = set(program.keys())
    frontiers = []

    while True:
        ready = []
        for k in unresolved:
            deps = program[k]["deps"]
            if all(d in resolved for d in deps):
                ready.append(k)

        if not ready:
            break

        frontier = []
        for k in sorted(ready):
            values[k] = program[k]["func"](values)
            resolved.add(k)
            unresolved.remove(k)
            frontier.append(k)

        frontiers.append(frontier)

    return values, frontiers, list(unresolved)

def run_system(program, arrivals_phase1, arrivals_phase2):
    # Phase 1
    prog_p1 = {k: program[k] for k in arrivals_phase1}
    values1, frontiers1, unresolved1 = resolve(prog_p1, arrivals_phase1)

    # Phase 2 (full program)
    values2, frontiers2, unresolved2 = resolve(program, arrivals_phase1 + arrivals_phase2)

    return {
        "phase1": {
            "frontiers": frontiers1,
            "unresolved": unresolved1
        },
        "final": {
            "values": values2,
            "frontiers": frontiers2,
            "unresolved": unresolved2
        }
    }

def hash_cert(obj):
    s = json.dumps(obj, sort_keys=True)
    return hashlib.sha256(s.encode()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    random.seed(args.seed)

    program = build_program()

    all_nodes = list(program.keys())

    # Phase 1 excludes Z
    phase1_nodes = [n for n in all_nodes if n != "Z"]
    phase2_nodes = ["Z"]

    arr_A_p1 = random.sample(phase1_nodes, len(phase1_nodes))
    arr_B_p1 = random.sample(phase1_nodes, len(phase1_nodes))

    arr_A_p2 = phase2_nodes[:]
    arr_B_p2 = phase2_nodes[:]

    A = run_system(program, arr_A_p1, arr_A_p2)
    B = run_system(program, arr_B_p1, arr_B_p2)

    match = A["final"]["values"] == B["final"]["values"]

    cert = hash_cert({
        "A": A,
        "B": B,
        "match": match
    })

    print("STOCRS v2 Fragmented Demo")
    print("Arrival A Phase1:", arr_A_p1)
    print("Arrival B Phase1:", arr_B_p1)
    print("Phase 1 Unresolved A:", A["phase1"]["unresolved"])
    print("Phase 1 Unresolved B:", B["phase1"]["unresolved"])
    print("Final Result Match:", "YES" if match else "NO")
    print("Final Values:", A["final"]["values"])
    print("Certificate:", cert)

if __name__ == "__main__":
    main()