import argparse
import hashlib
import json
import math
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any


@dataclass(frozen=True)
class Node:
    name: str
    op: str
    deps: Tuple[str, ...]
    value: Any = None


def structural_depth(nodes: Dict[str, Node], name: str, memo: Dict[str, int]) -> int:
    if name in memo:
        return memo[name]
    node = nodes[name]
    if not node.deps:
        memo[name] = 0
        return 0
    d = 1 + max(structural_depth(nodes, dep, memo) for dep in node.deps)
    memo[name] = d
    return d


def parent_signature(nodes: Dict[str, Node], name: str, memo: Dict[str, str]) -> str:
    if name in memo:
        return memo[name]
    node = nodes[name]
    if not node.deps:
        sig = f"{node.op}:root"
    else:
        child_sigs = [parent_signature(nodes, dep, memo) for dep in node.deps]
        joined = "|".join(sorted(child_sigs))
        sig = f"{node.op}:[{joined}]"
    memo[name] = sig
    return sig


def structural_rank(nodes: Dict[str, Node], name: str) -> Tuple[int, int, str, str]:
    depth_memo: Dict[str, int] = {}
    sig_memo: Dict[str, str] = {}
    depth = structural_depth(nodes, name, depth_memo)
    sig = parent_signature(nodes, name, sig_memo)
    dep_count = len(nodes[name].deps)
    return (depth, dep_count, sig, name)


def eval_op(op: str, args: List[Any], value: Any) -> Any:
    if op == "const":
        return value
    if op == "add":
        return args[0] + args[1]
    if op == "sub":
        return args[0] - args[1]
    if op == "mul":
        return args[0] * args[1]
    if op == "div":
        return args[0] / args[1]
    if op == "pow":
        return args[0] ** args[1]
    if op == "sin":
        return math.sin(args[0])
    if op == "cos":
        return math.cos(args[0])
    if op == "log1p":
        return math.log1p(args[0])
    if op == "neg":
        return -args[0]
    raise ValueError(f"Unsupported op: {op}")


class StructuralSystem:
    def __init__(self, name: str, declarations: List[Node], declared_order: List[str], drift_ppm: float, structural_correction_ms: float):
        self.name = name
        self.arrivals = [node.name for node in declarations]
        self.declared_nodes = {node.name: node for node in declarations}
        self.known_names = set(declared_order)
        self.nodes = {name: self.declared_nodes[name] for name in self.known_names}
        self.values: Dict[str, Any] = {}
        self.resolved_frontiers: List[List[str]] = []
        self.resolution_sequence: List[str] = []
        self.drift_ppm = drift_ppm
        self.structural_correction_ms = structural_correction_ms
        self.anchor_time_s = 1000000.0
        self.local_time_s = self.anchor_time_s
        self.used_time_for_correctness = False

    def step_time(self, ticks: int) -> None:
        drift_s = ticks * self.drift_ppm / 1_000_000.0
        correction_s = self.structural_correction_ms / 1000.0
        self.local_time_s = self.anchor_time_s + ticks + drift_s + correction_s

    def ready_frontier(self) -> List[str]:
        ready = []
        for name, node in self.nodes.items():
            if name in self.values:
                continue
            if all(dep in self.values for dep in node.deps):
                ready.append(name)
        return ready

    def resolve(self) -> None:
        while True:
            frontier = self.ready_frontier()
            if not frontier:
                break
            frontier_sorted = sorted(frontier, key=lambda n: structural_rank(self.nodes, n))
            self.resolved_frontiers.append(frontier_sorted)
            for name in frontier_sorted:
                node = self.nodes[name]
                args = [self.values[d] for d in node.deps]
                self.values[name] = eval_op(node.op, args, node.value)
                self.resolution_sequence.append(name)

    def unresolved(self) -> List[str]:
        return sorted([name for name in self.nodes if name not in self.values])

    def result_payload(self) -> Dict[str, Any]:
        return {
            "system": self.name,
            "arrivals": self.arrivals,
            "resolved_frontiers": self.resolved_frontiers,
            "resolution_sequence": self.resolution_sequence,
            "values": self.values,
            "unresolved": self.unresolved(),
            "local_time_s": round(self.local_time_s, 6),
            "used_time_for_correctness": self.used_time_for_correctness,
        }


SCENARIOS = {
    "branching": [
        Node("X", "const", tuple(), 2),
        Node("Y", "const", tuple(), 3),
        Node("A", "add", ("X", "Y")),
        Node("B", "mul", ("X", "Y")),
        Node("C", "add", ("A", "B")),
        Node("D", "pow", ("C", "X")),
        Node("E", "sub", ("D", "Y")),
    ],
    "diamond": [
        Node("U", "const", tuple(), 0.5),
        Node("V", "const", tuple(), 4),
        Node("P", "sin", ("U",)),
        Node("Q", "pow", ("V", "U")),
        Node("R", "add", ("P", "Q")),
        Node("S", "log1p", ("R",)),
        Node("T", "mul", ("S", "V")),
    ],
    "fragmented": [
        Node("I", "const", tuple(), 5),
        Node("J", "const", tuple(), 7),
        Node("K", "add", ("I", "J")),
        Node("L", "mul", ("K", "J")),
        Node("M", "sub", ("L", "I")),
        Node("N", "div", ("M", "J")),
    ],
}


def canonical_program_hash(nodes: List[Node]) -> str:
    payload = [
        {"name": n.name, "op": n.op, "deps": list(n.deps), "value": n.value}
        for n in sorted(nodes, key=lambda x: x.name)
    ]
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


def result_hash(payload: Dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode()).hexdigest()


def rounded_values(values: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in values.items():
        if isinstance(v, float):
            out[k] = round(v, 12)
        else:
            out[k] = v
    return out


def make_permutations(nodes: List[Node], seed: int) -> Tuple[List[Node], List[Node]]:
    rng_a = random.Random(seed)
    rng_b = random.Random(seed + 999)
    a = nodes[:]
    b = nodes[:]
    rng_a.shuffle(a)
    rng_b.shuffle(b)
    return a, b


def run_demo(scenario: str, seed: int, partial: bool) -> Dict[str, Any]:
    declarations = SCENARIOS[scenario]
    arrivals_a, arrivals_b = make_permutations(declarations, seed)
    all_names = [n.name for n in declarations]

    if partial and scenario == "fragmented":
        phase1_names = ["I", "J", "K", "L"]
        sys_a = StructuralSystem("A", arrivals_a, phase1_names, drift_ppm=240.0, structural_correction_ms=11.0)
        sys_b = StructuralSystem("B", arrivals_b, phase1_names, drift_ppm=-180.0, structural_correction_ms=-9.0)
        sys_a.step_time(90 * 24 * 3600)
        sys_b.step_time(90 * 24 * 3600)
        sys_a.resolve()
        sys_b.resolve()
        unresolved_phase1_a = sys_a.unresolved()
        unresolved_phase1_b = sys_b.unresolved()
        sys_a.nodes = {name: sys_a.declared_nodes[name] for name in all_names}
        sys_b.nodes = {name: sys_b.declared_nodes[name] for name in all_names}
        sys_a.resolve()
        sys_b.resolve()
        phase1 = {
            "unresolved_A": unresolved_phase1_a,
            "unresolved_B": unresolved_phase1_b,
        }
    else:
        sys_a = StructuralSystem("A", arrivals_a, all_names, drift_ppm=240.0, structural_correction_ms=11.0)
        sys_b = StructuralSystem("B", arrivals_b, all_names, drift_ppm=-180.0, structural_correction_ms=-9.0)
        sys_a.step_time(90 * 24 * 3600)
        sys_b.step_time(90 * 24 * 3600)
        sys_a.resolve()
        sys_b.resolve()
        phase1 = None

    values_a = rounded_values(sys_a.values)
    values_b = rounded_values(sys_b.values)
    final_match = values_a == values_b
    arrivals_different = sys_a.arrivals != sys_b.arrivals
    certificate_payload = {
        "scenario": scenario,
        "program_hash": canonical_program_hash(declarations),
        "arrivals_A": sys_a.arrivals,
        "arrivals_B": sys_b.arrivals,
        "values_A": values_a,
        "values_B": values_b,
        "resolution_sequence_A": sys_a.resolution_sequence,
        "resolution_sequence_B": sys_b.resolution_sequence,
        "result_match": final_match,
        "time_used_for_correctness": False,
    }
    certificate = result_hash(certificate_payload)
    return {
        "scenario": scenario,
        "seed": seed,
        "arrivals_different": arrivals_different,
        "time_used_for_correctness": False,
        "network_required_for_correctness": False,
        "result_match": final_match,
        "phase1": phase1,
        "system_A": sys_a.result_payload(),
        "system_B": sys_b.result_payload(),
        "certificate": certificate,
    }


def stress_test(scenario: str, runs: int, partial: bool) -> Dict[str, Any]:
    pass_count = 0
    certs = []
    for seed in range(runs):
        out = run_demo(scenario, seed, partial)
        if out["result_match"] and out["arrivals_different"] and not out["time_used_for_correctness"]:
            pass_count += 1
        certs.append(out["certificate"])
    payload = {
        "scenario": scenario,
        "runs": runs,
        "passes": pass_count,
        "all_passed": pass_count == runs,
        "certificate_digest": hashlib.sha256("".join(certs).encode()).hexdigest(),
    }
    return payload


def print_demo(out: Dict[str, Any]) -> None:
    print("STOCRS v1 Demo")
    print(f"Scenario: {out['scenario']}")
    print(f"Arrival A Different: {'YES' if out['arrivals_different'] else 'NO'}")
    print(f"Arrival B Different: {'YES' if out['arrivals_different'] else 'NO'}")
    print(f"Time Used for Correctness: {'NO' if not out['time_used_for_correctness'] else 'YES'}")
    print(f"Network Required for Correctness: {'NO' if not out['network_required_for_correctness'] else 'YES'}")
    print(f"Result Match: {'YES' if out['result_match'] else 'NO'}")
    if out["phase1"] is not None:
        print(f"Phase 1 Unresolved A: {out['phase1']['unresolved_A']}")
        print(f"Phase 1 Unresolved B: {out['phase1']['unresolved_B']}")
    print(f"System A Arrival Order: {out['system_A']['arrivals']}")
    print(f"System B Arrival Order: {out['system_B']['arrivals']}")
    print(f"System A Resolved Frontiers: {out['system_A']['resolved_frontiers']}")
    print(f"System B Resolved Frontiers: {out['system_B']['resolved_frontiers']}")
    print(f"System A Values: {json.dumps(rounded_values(out['system_A']['values']), sort_keys=True)}")
    print(f"System B Values: {json.dumps(rounded_values(out['system_B']['values']), sort_keys=True)}")
    print(f"Certificate: {out['certificate']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=sorted(SCENARIOS.keys()), default="branching")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--stress", type=int, default=0)
    parser.add_argument("--partial", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.stress > 0:
        payload = stress_test(args.scenario, args.stress, args.partial)
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print("STOCRS v1 Stress Test")
            print(f"Scenario: {payload['scenario']}")
            print(f"Runs: {payload['runs']}")
            print(f"Passes: {payload['passes']}")
            print(f"All Passed: {'YES' if payload['all_passed'] else 'NO'}")
            print(f"Certificate Digest: {payload['certificate_digest']}")
        return

    out = run_demo(args.scenario, args.seed, args.partial)
    if args.json:
        print(json.dumps(out, indent=2, sort_keys=True, default=str))
    else:
        print_demo(out)


if __name__ == "__main__":
    main()
