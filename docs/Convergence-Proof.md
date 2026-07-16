# **Convergence Proof — STOCRS**

**Scope-Bounded Deterministic Structural Convergence**

## **1. Purpose**

STOCRS models computation as a dependency-governed structural resolution process.

This document states the conditions under which the current STOCRS reference model produces the same supported final result.

The governing relation is:

`same complete compatible structure + same frozen rules -> same supported structural result`

This is a bounded claim about the declared STOCRS model.

It is not a proof that every computation, distributed protocol, or partial-sharing process converges without coordination.

---

## **2. Declared Structural Model**

Let a STOCRS program be a finite dependency structure:

`P = (V, E, F)`

where:

- `V` is a finite set of declared nodes
- `E` defines each node's declared dependencies
- `F` assigns a deterministic computation rule to each node

For the current reference implementation, the declared program is acyclic.

A node may be in one of three relevant conditions:

- **resolved** — its dependencies are available and its declared deterministic rule produces its supported value
- **unresolved** — one or more required dependencies are not resolved
- **conflicted** — available claim evidence is incompatible with itself or with the value determined by declared structure

The runtime does not use time, arrival order, or claim multiplicity as computational authority.

---

## **3. Deterministic Resolution Rule**

For a fixed declared program and fixed available structure, resolution proceeds by repeatedly identifying nodes whose declared dependencies are resolved.

For each structurally ready node:

`value(node) = F_node(resolved_dependency_values)`

Because each rule in `F` is deterministic:

`same dependency values + same rule -> same node value`

The current runtime evaluates ready nodes in a sorted frontier, but the supported values do not depend on fragment arrival order.

The decisive condition is structural readiness.

---

## **4. Incomplete Structure**

If a node requires a dependency that is not resolved, that node remains unresolved.

Formally:

`missing required dependency -> unresolved`

No value is invented merely because a result is requested.

Therefore, incomplete structure may reach a partial closure in which:

- some nodes are resolved
- some nodes remain unresolved
- no further progress is possible without additional compatible structure

This is a valid STOCRS state.

---

## **5. Conflict Handling**

Claims are evidence about a declared computation.

They do not replace declared computational authority.

The current runtime follows these rules:

`one distinct claim matching declared computation -> compatible evidence`

`one distinct claim disagreeing with declared computation -> claim_vs_structure`

`more than one distinct claim value -> multi_value_conflict`

The authority rule is:

`claim multiplicity != structural authority`

Therefore, a repeated incompatible claim cannot become authoritative by majority support.

If a required node is conflicted, a dependent node lacking that resolved dependency remains unresolved.

For example:

`X1 claims = [2, 9] -> X1 conflicted`

`A1 depends on X1 -> A1 unresolved`

When conflicting evidence is corrected or removed, the structure may be evaluated again and resolution may proceed.

This recovery is a new evaluation under corrected compatible evidence.

It is not majority-based conflict resolution.

---

## **6. Termination for a Fixed Finite Acyclic Structure**

Consider one resolution run over a fixed finite acyclic program subset.

During that run, each iteration does one of two things:

- resolves at least one structurally ready node
- records a conflict for a ready node and prevents that node from being resolved from incompatible evidence

A node removed from active consideration during the run is not reconsidered within that same run.

Because the declared node set is finite, the process must terminate after finitely many node decisions.

Termination therefore means:

`finite fixed structure -> finite resolution process`

Termination does not imply that every node resolves.

The terminal state may contain unresolved dependents if required structure is missing or conflicted.

---

## **7. Uniqueness of Supported Values**

Assume:

- the declared program is fixed
- the relevant structure is complete
- the structure is compatible
- the deterministic rules are fixed
- the dependency graph is acyclic

Then each root node has one value determined by its declared rule.

Every non-root node receives one fixed tuple of dependency values.

Its deterministic rule therefore produces one fixed value.

By induction over dependency depth:

`same complete compatible structure + same frozen rules -> same value for every resolvable node`

Therefore, the supported final value map is unique under the declared assumptions.

---

## **8. Arrival-Order Independence**

Different systems may receive or store the same declared nodes in different orders.

Let:

`A` and `B`

be two different arrival histories that result in the same complete compatible declared structure.

Then:

`structure(A) = structure(B)`

and, with the same frozen rules:

`resolve(structure(A)) = resolve(structure(B))`

Therefore:

`same final structure + same rules -> same supported final result`

The stronger expression:

`arrival_A != arrival_B -> result_A == result_B`

is valid only when both arrival histories yield the same relevant complete compatible structure under the same rules.

Arrival order is therefore not resolution authority.

---

## **9. What the Canonical Demo Demonstrates**

The canonical demo begins with five systems holding different incomplete fragments.

Across the intermediate phases:

- the systems hold different structural views
- bounded sharing adds some structure
- unresolved nodes remain
- local-time values differ

The bounded-sharing phases do not prove that bounded sharing alone guarantees complete dissemination.

In the final phase, the complete declared node set is explicitly available to every system.

Each system then evaluates:

`same complete compatible structure + same frozen rules`

The observed result is:

`Final Complete OK: YES`

`Final Match OK: YES`

`Final Node Count: 20`

`Final E1: 202`

The tested final result is therefore invariant across the different final node orders used by the canonical reference case.

---

## **10. Structural Closure**

For a fixed available structure, structural closure is reached when no additional node can resolve under the declared rules.

At closure, a node may be:

- resolved
- unresolved because required dependencies are unavailable
- blocked indirectly because a required dependency is conflicted

For a complete compatible acyclic structure, all declared nodes in the reference model resolve.

For incomplete or incompatible structure, closure may remain partial.

Therefore:

`closure != universal completeness`

Instead:

`closure = no further resolution possible from the currently available compatible structure`

---

## **11. Conditional Convergence Theorem**

For the current STOCRS reference model, assume that multiple systems eventually hold:

- the same declared finite acyclic program structure
- the same complete compatible node set
- the same frozen deterministic rules

Then each system computes the same supported final value map.

Formally:

P_A = P_B

S_A = S_B

implies:

resolve(P_A, S_A) = resolve(P_B, S_B)

where S_A and S_B denote the relevant complete compatible available structure for each system. Equality of P_A and P_B includes equality of the declared dependency structure and deterministic frozen rules. The resulting equality concerns the supported structural result.

Thus, under the declared conditions:

**STOCRS converges by structural equivalence.**

The convergence claim does not depend on:

- wall-clock equality
- timestamp equality
- fragment arrival order
- continuous synchronization
- claim majority

It does depend on eventual equivalence of the relevant complete compatible structure and deterministic rules.

---

## **12. What This Proof Does Not Establish**

This document does not establish that:

- every arbitrary program is order-independent
- cyclic dependency structures always resolve
- bounded sharing guarantees eventual delivery of all required structure
- every distributed system can eliminate coordination
- communication is unnecessary
- conflicting evidence resolves itself through repetition
- all serialized traces are identical under arbitrary histories
- STOCRS is a consensus protocol
- the current reference implementation is a production safety certification

The proof concerns the deterministic supported result under the declared structural assumptions.

---

## **13. Reference Invariants**

The current STOCRS model is governed by these bounded invariants:

`same complete compatible structure + same frozen rules -> same supported structural result`

`incomplete structure -> unresolved`

`multi-value claim conflict -> conflicted node`

`structure-incompatible claim -> conflicted node`

`required dependency not resolved -> dependent node unresolved`

`claim multiplicity != structural authority`

`corrected compatible evidence -> resolution may proceed again`

---

## **14. Conclusion**

STOCRS does not prove that all computation is independent of time, order, or coordination.

It demonstrates a narrower structural result:

**when the same complete compatible dependency structure is evaluated under the same deterministic frozen rules, the supported computational result is the same, even when fragment arrival order and local clock values differ.**

The central relation is:

`same complete compatible structure + same frozen rules -> same supported structural result`

### **Final Insight**

Time may describe execution.

Arrival order may describe transport history.

Claims may provide evidence.

Within the STOCRS reference model, none of them replace declared structure and deterministic rules as computational authority.
