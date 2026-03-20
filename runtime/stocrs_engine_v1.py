import argparse
import hashlib
import json


def build_program():
    program = {}

    program["X1"] = {"deps": [], "func": lambda values: 2}
    program["X2"] = {"deps": [], "func": lambda values: 3}
    program["X3"] = {"deps": [], "func": lambda values: 5}
    program["X4"] = {"deps": [], "func": lambda values: 7}

    program["A1"] = {"deps": ["X1", "X2"], "func": lambda values: values["X1"] + values["X2"]}
    program["A2"] = {"deps": ["X2", "X3"], "func": lambda values: values["X2"] * values["X3"]}
    program["A3"] = {"deps": ["X3", "X4"], "func": lambda values: values["X3"] + values["X4"]}
    program["A4"] = {"deps": ["X1", "X4"], "func": lambda values: values["X1"] * values["X4"]}

    program["Z1"] = {"deps": [], "func": lambda values: 17}
    program["Z2"] = {"deps": [], "func": lambda values: 19}

    program["B1"] = {"deps": ["A1", "A2"], "func": lambda values: values["A1"] + values["A2"]}
    program["B2"] = {"deps": ["A2", "A3"], "func": lambda values: values["A2"] - values["A3"]}
    program["B3"] = {"deps": ["A3", "A4"], "func": lambda values: values["A3"] + values["A4"]}
    program["B4"] = {"deps": ["A1", "A4"], "func": lambda values: values["A1"] + values["A4"]}

    program["C1"] = {"deps": ["B1", "B2"], "func": lambda values: values["B1"] + values["B2"]}
    program["C2"] = {"deps": ["B2", "B3", "Z1"], "func": lambda values: values["B2"] + values["B3"] + values["Z1"]}
    program["C3"] = {"deps": ["B3", "B4", "Z2"], "func": lambda values: values["B3"] + values["B4"] + values["Z2"]}

    program["D1"] = {"deps": ["C1", "C2"], "func": lambda values: values["C1"] * 2 + values["C2"]}
    program["D2"] = {"deps": ["C2", "C3"], "func": lambda values: values["C2"] + values["C3"]}

    program["E1"] = {"deps": ["D1", "D2"], "func": lambda values: values["D1"] + values["D2"]}

    return program


def reconstruct_time(anchor_s, elapsed_s, drift_ppm, structural_correction_s=0.0):
    return round(
        anchor_s + elapsed_s * (1.0 + drift_ppm / 1000000.0) + structural_correction_s,
        6,
    )


def normalize_claims(claims):
    normalized = {}
    if not claims:
        return normalized

    for node, raw in claims.items():
        if isinstance(raw, list):
            normalized[node] = list(raw)
        else:
            normalized[node] = [raw]

    return normalized


def choose_claim_value(values):
    counts = {}
    for value in values:
        key = json.dumps(value, sort_keys=True, separators=(",", ":"))
        if key not in counts:
            counts[key] = {"value": value, "count": 0}
        counts[key]["count"] += 1

    ranked = sorted(
        counts.values(),
        key=lambda item: (-item["count"], json.dumps(item["value"], sort_keys=True, separators=(",", ":"))),
    )

    if len(ranked) == 1:
        return {
            "status": "accepted",
            "value": ranked[0]["value"],
            "support": ranked[0]["count"],
            "distinct_values": 1,
        }

    if ranked[0]["count"] > ranked[1]["count"]:
        return {
            "status": "accepted",
            "value": ranked[0]["value"],
            "support": ranked[0]["count"],
            "distinct_values": len(ranked),
        }

    return {
        "status": "conflict",
        "value": None,
        "support": ranked[0]["count"],
        "distinct_values": len(ranked),
    }


def resolve(program_subset, claims=None):
    values = {}
    resolved = set()
    unresolved = set(program_subset.keys())
    frontiers = []
    conflicts = {}
    claims = normalize_claims(claims)

    while True:
        ready = []
        for node in unresolved:
            deps = program_subset[node]["deps"]
            if all(dep in resolved for dep in deps):
                ready.append(node)

        if not ready:
            break

        frontier = sorted(ready)
        resolved_now = []

        for node in frontier:
            node_claims = claims.get(node, [])

            if node_claims:
                claim_decision = choose_claim_value(node_claims)

                if claim_decision["status"] == "accepted":
                    if program_subset[node]["deps"]:
                        computed_value = program_subset[node]["func"](values)
                        if claim_decision["value"] == computed_value:
                            values[node] = computed_value
                            resolved.add(node)
                            unresolved.remove(node)
                            resolved_now.append(node)
                        else:
                            conflicts[node] = {
                                "type": "claim_vs_structure",
                                "claims": node_claims,
                                "computed_value": computed_value,
                            }
                            unresolved.remove(node)
                    else:
                        values[node] = claim_decision["value"]
                        resolved.add(node)
                        unresolved.remove(node)
                        resolved_now.append(node)
                else:
                    conflicts[node] = {
                        "type": "multi_value_conflict",
                        "claims": node_claims,
                    }
                    unresolved.remove(node)
            else:
                values[node] = program_subset[node]["func"](values)
                resolved.add(node)
                unresolved.remove(node)
                resolved_now.append(node)

        if not resolved_now:
            break

        frontiers.append(resolved_now)

    blocked = sorted(unresolved)
    return values, frontiers, blocked, conflicts


def initial_fragment_for_system(index):
    fragments = [
        ["X1", "A1", "B1", "C1", "D1"],
        ["X2", "A2", "B2", "C2", "D2"],
        ["X3", "A3", "B3", "C3", "E1"],
        ["X4", "A4", "B4", "C3", "D2"],
        ["Z1", "Z2", "B2", "B3", "C2"],
        ["A1", "A2", "C1", "D1", "E1"],
    ]
    return fragments[index % len(fragments)][:]


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


def run_system(system_name, program, known_nodes, anchor_s, elapsed_s, drift_ppm, claims=None):
    program_subset = {node: program[node] for node in known_nodes if node in program}
    active_claims = {}
    if claims:
        for node, values in claims.items():
            if node in program_subset:
                active_claims[node] = values

    values, frontiers, unresolved, conflicts = resolve(program_subset, claims=active_claims)
    local_time_s = reconstruct_time(anchor_s, elapsed_s, drift_ppm, 0.0)

    return {
        "system": system_name,
        "known_nodes": list(known_nodes),
        "known_count": len(known_nodes),
        "local_time_s": local_time_s,
        "frontiers": frontiers,
        "unresolved": unresolved,
        "conflicts": conflicts,
        "values": values,
    }


def hash_obj(obj):
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_conflict_demo():
    program = build_program()

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

    majority_run = run_system(
        system_name="S1",
        program=program,
        known_nodes=["X1", "X2", "A1"],
        anchor_s=1000.0,
        elapsed_s=60.0,
        drift_ppm=0.0,
        claims={"X1": [2, 2, 9], "X2": [3, 3]},
    )

    result = {
        "stable_run": stable_run,
        "conflict_run": conflict_run,
        "majority_run": majority_run,
    }
    result["certificate"] = hash_obj(result)
    return result


def print_conflict_demo(result):
    print("STOCRS Conflict Resolution Demo")
    print()

    print("Stable Run")
    print(f"Resolved Values: {result['stable_run']['values']}")
    print(f"Unresolved: {result['stable_run']['unresolved']}")
    print(f"Conflicts: {result['stable_run']['conflicts']}")
    print()

    print("Conflict Run")
    print(f"Resolved Values: {result['conflict_run']['values']}")
    print(f"Unresolved: {result['conflict_run']['unresolved']}")
    print(f"Conflicts: {result['conflict_run']['conflicts']}")
    print()

    print("Majority Support Run")
    print(f"Resolved Values: {result['majority_run']['values']}")
    print(f"Unresolved: {result['majority_run']['unresolved']}")
    print(f"Conflicts: {result['majority_run']['conflicts']}")
    print()

    print(f"Certificate: {result['certificate']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--conflict-demo", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.conflict_demo:
        result = build_conflict_demo()
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print_conflict_demo(result)


if __name__ == "__main__":
    main()