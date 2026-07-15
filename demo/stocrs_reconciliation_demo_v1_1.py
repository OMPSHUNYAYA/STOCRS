import json
import hashlib
import random
import time
import argparse


def build_program():
    program = {}

    program["ACC1_BASE"] = {
        "deps": [],
        "func": lambda values: 100
    }
    program["ACC2_BASE"] = {
        "deps": [],
        "func": lambda values: 50
    }
    program["ACC3_BASE"] = {
        "deps": [],
        "func": lambda values: 75
    }

    program["ACC1_CREDIT"] = {
        "deps": ["ACC1_BASE"],
        "func": lambda values: values["ACC1_BASE"] + 20
    }
    program["ACC2_DEBIT"] = {
        "deps": ["ACC2_BASE"],
        "func": lambda values: values["ACC2_BASE"] - 10
    }
    program["ACC3_CREDIT"] = {
        "deps": ["ACC3_BASE"],
        "func": lambda values: values["ACC3_BASE"] + 5
    }

    program["ACC1_FINAL"] = {
        "deps": ["ACC1_CREDIT"],
        "func": lambda values: values["ACC1_CREDIT"]
    }
    program["ACC2_FINAL"] = {
        "deps": ["ACC2_DEBIT"],
        "func": lambda values: values["ACC2_DEBIT"]
    }
    program["ACC3_FINAL"] = {
        "deps": ["ACC3_CREDIT"],
        "func": lambda values: values["ACC3_CREDIT"]
    }

    program["TOTAL_BALANCE"] = {
        "deps": ["ACC1_FINAL", "ACC2_FINAL", "ACC3_FINAL"],
        "func": lambda values: (
            values["ACC1_FINAL"] +
            values["ACC2_FINAL"] +
            values["ACC3_FINAL"]
        )
    }

    return program


def resolve(program_subset):
    values = {}
    resolved = set()
    unresolved = set(program_subset.keys())
    frontiers = []

    while True:
        ready = []
        for node in unresolved:
            deps = program_subset[node]["deps"]
            if all(dep in resolved for dep in deps):
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


def hash_obj(obj):
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def shuffled(nodes, rng):
    data = list(nodes)
    rng.shuffle(data)
    return data


def build_initial_fragments(rng):
    systems = {
        "S1": shuffled(["ACC1_CREDIT", "ACC2_DEBIT", "ACC1_FINAL"], rng),
        "S2": shuffled(["ACC1_BASE", "ACC3_CREDIT", "ACC2_FINAL"], rng),
        "S3": shuffled(["ACC2_BASE", "ACC3_BASE", "ACC3_FINAL"], rng),
        "S4": shuffled(["TOTAL_BALANCE", "ACC2_DEBIT", "ACC3_CREDIT"], rng),
    }
    return systems


def full_completion_nodes():
    return [
        "ACC1_BASE",
        "ACC2_BASE",
        "ACC3_BASE",
        "ACC1_CREDIT",
        "ACC2_DEBIT",
        "ACC3_CREDIT",
        "ACC1_FINAL",
        "ACC2_FINAL",
        "ACC3_FINAL",
        "TOTAL_BALANCE",
    ]


def merge_unique(current_nodes, incoming_nodes):
    merged = []
    seen = set()

    for node in list(current_nodes) + list(incoming_nodes):
        if node not in seen:
            seen.add(node)
            merged.append(node)

    return merged


def run_system(program, known_nodes):
    subset = {node: program[node] for node in known_nodes if node in program}
    values, frontiers, unresolved = resolve(subset)
    return {
        "known_nodes": list(known_nodes),
        "known_count": len(known_nodes),
        "frontiers": frontiers,
        "unresolved": unresolved,
        "values": values,
    }


def run_demo(seed):
    rng = random.Random(seed)
    program = build_program()
    initial = build_initial_fragments(rng)
    completion = full_completion_nodes()

    phase1 = {}
    phase2 = {}

    for system_name, nodes in initial.items():
        phase1[system_name] = run_system(program, nodes)

    for system_name, nodes in initial.items():
        merged_nodes = merge_unique(nodes, completion)
        phase2[system_name] = run_system(program, merged_nodes)

    final_values = {}
    final_hashes = {}
    reference_state = None
    all_match = True
    final_complete = True
    phase1_all_unresolved = True

    for system_name, result in phase1.items():
        if not result["unresolved"]:
            phase1_all_unresolved = False

    for system_name, result in phase2.items():
        values = result["values"]
        unresolved = result["unresolved"]

        system_state = {
            "ACC1_FINAL": values.get("ACC1_FINAL"),
            "ACC2_FINAL": values.get("ACC2_FINAL"),
            "ACC3_FINAL": values.get("ACC3_FINAL"),
            "TOTAL_BALANCE": values.get("TOTAL_BALANCE"),
        }

        final_values[system_name] = system_state
        final_hashes[system_name] = hash_obj(system_state)

        if unresolved:
            final_complete = False

        if reference_state is None:
            reference_state = system_state
        elif system_state != reference_state:
            all_match = False

    certificate_payload = {
        "seed": seed,
        "phase1": phase1,
        "phase2": phase2,
        "final_values": final_values,
        "final_hashes": final_hashes,
        "phase1_all_unresolved": phase1_all_unresolved,
        "final_complete": final_complete,
        "all_match": all_match,
    }

    certificate = hash_obj(certificate_payload)

    return {
        "name": "STOCRS Reconciliation Demo v1.1",
        "seed": seed,
        "systems": 4,
        "no_logs": True,
        "no_timestamps": True,
        "no_order_required": True,
        "phase1": phase1,
        "phase2": phase2,
        "phase1_all_unresolved": phase1_all_unresolved,
        "final_values": final_values,
        "final_hashes": final_hashes,
        "final_complete": final_complete,
        "all_match": all_match,
        "certificate": certificate,
    }


def print_text(result, elapsed_s):
    print("STOCRS Reconciliation Demo v1.1")
    print()
    print(f"Seed: {result['seed']}")
    print(f"Systems: {result['systems']}")
    print()
    print("No Logs: YES")
    print("No Timestamps: YES")
    print("No Order Required: YES")
    print()
    print("Phase 1 Unresolved Exists: " + (
        "YES" if any(result["phase1"][s]["unresolved"] for s in result["phase1"]) else "NO"
    ))
    print("Phase 1 All Systems Unresolved: " + (
        "YES" if result["phase1_all_unresolved"] else "NO"
    ))
    print("Final Complete OK: " + ("YES" if result["final_complete"] else "NO"))
    print("Final Match OK: " + ("YES" if result["all_match"] else "NO"))
    print()

    for system_name in sorted(result["phase1"].keys()):
        print(f"{system_name} Phase 1 Known: {result['phase1'][system_name]['known_count']}")
        print(f"{system_name} Phase 1 Unresolved Count: {len(result['phase1'][system_name]['unresolved'])}")
        print()

    for system_name in sorted(result["final_values"].keys()):
        state = result["final_values"][system_name]
        print(f"{system_name} ACC1_FINAL: {state['ACC1_FINAL']}")
        print(f"{system_name} ACC2_FINAL: {state['ACC2_FINAL']}")
        print(f"{system_name} ACC3_FINAL: {state['ACC3_FINAL']}")
        print(f"{system_name} TOTAL_BALANCE: {state['TOTAL_BALANCE']}")
        print()

    print(f"Elapsed Runtime: {elapsed_s:.6f} s")
    print(f"Certificate: {result['certificate']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=101)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    started = time.perf_counter()
    result = run_demo(args.seed)
    elapsed_s = time.perf_counter() - started

    if args.json:
        output = dict(result)
        output["elapsed_runtime_s"] = round(elapsed_s, 6)
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        print_text(result, elapsed_s)


if __name__ == "__main__":
    main()