# ⭐ **FAQ — STOCRS**

**Shunyaya Timeless Computation**

**Deterministic • Structure-Driven • Explicit Incompleteness • Conflict-Aware • Replay-Verifiable**

---

**No GPS • No NTP • No Internet • No Global Clock Used for Correctness in the Declared Reference Cases**

---

# **SECTION A — Purpose & Positioning**

## **A1. What is STOCRS?**

STOCRS is a **reference model for deterministic structural computation**.

Instead of using time, fragment arrival order, or claim multiplicity as computational authority, STOCRS resolves values from:

- declared nodes
- declared dependencies
- deterministic frozen rules
- compatible available structure

The core relation is:

`same complete compatible structure + same frozen rules -> same supported structural result`

---

## **A2. What problem does STOCRS explore?**

Many systems use mechanisms such as:

- ordered execution
- timestamps
- synchronized clocks
- continuous coordination
- replay histories

STOCRS asks a narrower architectural question:

**Can some computational results be determined directly from declared dependency structure rather than from time or arrival order?**

The current reference implementation demonstrates that this is possible within its declared cases.

---

## **A3. Does STOCRS prove that all computation can ignore time or order?**

No.

STOCRS does not claim that:

- every computation is order-independent
- every distributed system can eliminate coordination
- every partial-sharing process converges automatically
- communication or execution infrastructure is unnecessary

Its claim is bounded to the declared structural model and verified reference cases.

---

## **A4. Does STOCRS replace existing distributed systems?**

No.

STOCRS is not:

- a distributed database
- a consensus protocol
- a universal replacement for execution systems
- a production deployment architecture by itself

It is a structural reference model that may inform systems in which deterministic resolution from explicit dependencies is useful.

---

## **A5. Is STOCRS probabilistic or machine-learning based?**

No.

The reference implementation uses:

- no machine learning
- no probabilistic selection
- no model training
- no stochastic resolution authority

The canonical demo uses seeded shuffling to vary fragment order, but the supported result is determined by declared structure and deterministic rules.

---

## **A6. Why does the STOCRS demo mention no GPS, no NTP, and no internet?**

Because the canonical reference case demonstrates that those external services are not used to determine the supported computational result.

The demo reports:

`No GPS: YES`

`No NTP: YES`

`No Internet: YES`

`Time Used for Correctness: NO`

This does not mean GPS, NTP, internet connectivity, or clocks have no operational value.

It means they are not used as computational authority in the declared reference case.

---

## **A7. Is STOCRS mainly about distributed systems?**

Distributed and intermittently connected systems are natural areas of relevance, but STOCRS is more general.

Its central concern is:

**dependency-governed deterministic resolution**

Possible areas of relevance include:

- distributed computation
- edge and offline systems
- deterministic replay
- recovery and reconstruction
- data reconciliation
- audit-oriented computation
- conflict-aware structural processing

Production use requires independent validation beyond the current reference implementation.

---

# **SECTION B — Structural Computation Model**

## **B1. What is the core idea behind STOCRS?**

STOCRS represents computation as a dependency-governed structure.

Each node:

- has declared dependencies
- becomes structurally ready when those dependencies are resolved
- is evaluated by a declared deterministic rule
- remains unresolved when required dependencies are unavailable

The central idea is:

`structure determines resolvability`

`declared computation determines supported value`

---

## **B2. What is the core resolution rule?**

Conceptually:

`resolve(structure) -> evaluate structurally ready nodes -> repeat`

For a ready node:

`value(node) = declared_rule(resolved_dependency_values)`

Resolution continues until no additional node can resolve from the currently available compatible structure.

---

## **B3. How is the supported result determined?**

Within the current reference model, the supported result is determined by:

- the declared program structure
- the available compatible node set
- the deterministic computation rules

Time, arrival order, and claim majority do not replace that authority.

---

## **B4. Why is time not used as computational authority?**

The reference model does not use time to decide what a node means or what value it should produce.

A node resolves when its declared dependencies are available and compatible.

Local time may still be calculated or observed, but it does not determine the supported computational value.

---

## **B5. What is a fragment in STOCRS?**

A fragment is a partial subset of the declared computation structure.

Different systems may begin with different fragments.

A fragment may contain:

- resolvable nodes
- unresolved nodes
- nodes whose dependencies are absent

Incomplete fragments are valid intermediate states.

---

## **B6. Can STOCRS operate with incomplete information?**

Yes.

Incomplete structure may remain partially resolved.

If a required dependency is unavailable:

`missing required dependency -> unresolved`

STOCRS does not invent a value to force completion.

---

## **B7. Do all systems need the same starting structure?**

No.

The canonical demo begins with different incomplete fragments across systems.

The verified final agreement occurs when the systems later evaluate the same complete compatible declared structure under the same frozen rules.

---

## **B8. What happens if structure never completes?**

Then some nodes may remain unresolved indefinitely.

That is a valid outcome.

STOCRS does not claim that every incomplete state must eventually become complete.

---

## **B9. Does bounded sharing guarantee complete dissemination?**

No.

The canonical demo includes bounded intermediate sharing, but those phases intentionally remain incomplete.

The demo later makes the complete declared node set explicitly available to every system.

Therefore:

**bounded sharing demonstrates incomplete structural progression, not a proof of guaranteed dissemination.**

---

# **SECTION C — Multi-System Behavior**

## **C1. How do multiple systems behave in the canonical demo?**

The systems:

- begin with different incomplete fragments
- hold different intermediate structural views
- use different fragment orders
- have different local-time values
- remain unresolved through bounded intermediate phases

In the final phase, each system receives the same complete declared structure.

They then produce the same supported final result.

---

## **C2. What happens when systems receive more compatible structure?**

Additional compatible structure may satisfy previously missing dependencies.

This can allow more nodes to resolve.

However, additional structure does not automatically guarantee full completion unless all required dependencies eventually become available.

---

## **C3. What if systems have different local times?**

Different local-time values do not determine the supported computational result in the reference model.

The canonical demo intentionally uses different reconstructed local-time values while the final supported result remains the same.

---

## **C4. What if systems receive fragments in different orders?**

Different arrival orders may produce different intermediate views.

However, when those histories result in the same relevant complete compatible structure under the same frozen rules:

`same final structure + same rules -> same supported final result`

Arrival order is therefore not resolution authority in the declared reference case.

---

## **C5. Do systems need continuous communication?**

Not for the tested final resolution once the same complete compatible structure is locally available.

However, STOCRS does not claim that required structure can arrive without communication.

Transport, persistence, and dissemination remain operational concerns.

---

## **C6. Must all systems be online at the same time?**

Not in the reference model.

Systems may hold different incomplete states at different times.

The convergence claim depends on eventual equivalence of the relevant complete compatible structure, not simultaneous online presence.

---

# **SECTION D — Unresolved State Model**

## **D1. What is an unresolved state?**

A node is unresolved when one or more required dependencies are not resolved.

This is not automatically an error.

It means:

**the currently available structure is insufficient to support that node's value.**

---

## **D2. Why is unresolved not considered failure?**

Because incomplete structure does not justify inventing a result.

STOCRS treats unresolved as an explicit structural state rather than forcing premature completion.

---

## **D3. When does resolution occur?**

A node may resolve when:

- all declared dependencies are resolved
- its declared rule can be evaluated
- available claim evidence, when present, is compatible with declared computation

---

## **D4. Can unresolved state persist across many phases?**

Yes.

The canonical demo intentionally preserves unresolved nodes through multiple bounded-sharing phases.

This demonstrates that incomplete structure can remain explicit without forcing an unsupported result.

---

## **D5. What is structural closure?**

Structural closure is reached when no additional node can resolve from the currently available compatible structure.

Closure does not always mean full completion.

A closed state may still contain unresolved nodes if required structure is absent or conflicted.

---

# **SECTION E — Convergence**

## **E1. What guarantees convergence in STOCRS?**

The current convergence claim is conditional.

Multiple systems produce the same supported final result when they eventually hold:

- the same declared finite acyclic program structure
- the same complete compatible node set
- the same frozen deterministic rules

Then:

`same complete compatible structure + same frozen rules -> same supported structural result`

---

## **E2. What ensures all systems reach the same supported result?**

The reference program is deterministic and acyclic.

For the same complete compatible structure:

- root values are fixed by declared rules
- each dependent node receives the same dependency values
- each deterministic rule therefore produces the same value

This yields the same supported final value map.

---

## **E3. What does the canonical demo actually demonstrate?**

It demonstrates that five systems can:

- begin with different incomplete fragments
- remain unresolved through several phases
- use different fragment orders
- hold different local-time values
- later receive the same complete compatible declared structure
- produce the same supported final result

It does not prove that partial sharing alone guarantees eventual complete structure.

---

## **E4. What is the final result in the canonical demo?**

The canonical reference case reports:

`Final Complete OK: YES`

`Final Match OK: YES`

`Final Node Count: 20`

`Final E1: 202`

---

## **E5. Is the convergence claim universal?**

No.

It is a bounded claim under the declared STOCRS assumptions.

For details, see:

`docs/Convergence-Proof.md`

---

# **SECTION F — Determinism and Verification**

## **F1. Is STOCRS deterministic?**

Within the declared model, yes.

The governing relation is:

`same complete compatible structure + same frozen rules -> same supported structural result`

---

## **F2. How is reproducibility verified?**

The current verification path uses:

- deterministic canonical reference output
- deterministic certificates
- frozen SHA-256 file hashes
- exact canonical JSON reproduction
- reconciliation semantic verification
- conflict-authority regression testing
- GitHub Actions workflow verification

---

## **F3. What is replay verification?**

Replay verification checks whether the declared reference case can be executed again and reproduce the expected result.

The canonical JSON output is compared exactly with the frozen canonical reference artifact.

---

## **F4. What does the canonical certificate bind?**

The canonical certificate is:

`SHA256(certificate_payload)`

It binds the deterministic structural data included in that declared payload.

It does not certify:

- source-code identity
- deployment safety
- performance
- production readiness

Exact file identity is verified separately through the SHA-256 freeze records.

---

## **F5. Why is file hashing separate from certificates?**

Because the two mechanisms serve different purposes.

`certificate -> deterministic declared result payload`

`FREEZE SHA256 -> exact file identity`

The verification bundle checks both.

---

## **F6. Why was elapsed runtime removed from the canonical JSON?**

Elapsed runtime varies between executions and environments.

Removing it from the canonical JSON allows exact deterministic comparison with the frozen canonical reference artifact.

---

## **F7. Why does the reconciliation reference artifact still contain elapsed runtime?**

The reconciliation artifact predates the canonical cleanup and retains its recorded runtime field.

Therefore, reconciliation verification compares its declared semantic result fields and certificate rather than requiring byte-identical regeneration.

---

## **F8. What are the current primary verification files?**

The current reference path includes:

- `demo/stocrs_canonical_demo_v1_2.py`
- `runtime/stocrs_engine_v1_1.py`
- `reference_outputs/`
- `VERIFY/`
- `.github/workflows/verify.yml`

The illustrative POC demo is not the primary verification authority.

---

# **SECTION G — Conflict Handling**

## **G1. What happens with conflicting claims?**

If more than one distinct claim value is present for a ready node:

`more than one distinct claim value -> multi_value_conflict`

The node does not resolve from those conflicting claims.

---

## **G2. What happens when a claim disagrees with declared computation?**

If there is one distinct claimed value but it disagrees with the value computed from declared structure:

`claim_vs_structure`

The incompatible claim is not allowed to override the declared computation.

---

## **G3. Can majority support override declared structure?**

No.

The authority rule is:

`claim multiplicity != structural authority`

For example, if declared structure computes:

`X1 = 2`

then:

`[9, 9]`

does not make `9` authoritative.

Likewise:

`[9, 9, 2]`

is still conflicting evidence and cannot override declared structure.

---

## **G4. What happens to dependent nodes when a required node is conflicted?**

They remain unresolved if the required dependency is not resolved.

For example:

`X1 claims = [2, 9] -> X1 conflicted`

`A1 depends on X1 -> A1 unresolved`

---

## **G5. How does recovery work?**

Recovery occurs through a new evaluation after conflicting evidence is corrected or removed.

Then compatible structure may resolve again.

This is not:

- majority voting
- structural dominance by repetition
- claim reinforcement

It is re-evaluation under corrected compatible evidence.

---

## **G6. Can adversarial inputs ever affect STOCRS?**

The reference implementation contains bounded conflict checks for the specific declared cases.

It should not be interpreted as a universal adversarial-resilience guarantee.

Broader hostile-input handling would require additional validation and engineering.

---

# **SECTION H — Operating Requirements**

## **H1. What is required to run STOCRS?**

For the current reference implementation:

- Python 3.9+
- standard library only
- no external Python dependencies

The GitHub Actions workflow currently runs with Python 3.10.

---

## **H2. Does the reference demo require network connectivity?**

No.

The canonical and runtime demonstrations run fully offline.

---

## **H3. Does STOCRS require GPS, NTP, or a global clock for the tested computational result?**

No.

Those services are not used as computational authority in the declared reference cases.

---

## **H4. Does STOCRS require special hardware?**

No.

The current reference implementation runs in a standard Python environment.

---

# **SECTION I — Relation to Other Ideas**

## **I1. Is STOCRS the same as consensus?**

No.

Consensus protocols address agreement among participants under specific communication and fault assumptions.

STOCRS addresses deterministic resolution from declared structure once the relevant complete compatible structure is available.

It is not a consensus protocol.

---

## **I2. Is STOCRS the same as CRDTs or eventual consistency?**

No.

There may be conceptual overlap around convergence and distributed state, but STOCRS uses a different declared model centered on dependency-governed structural resolution.

The repository does not claim that STOCRS replaces CRDTs or eventual-consistency systems.

---

## **I3. Is STOCRS just a scheduler?**

No.

A scheduler decides when or in what order work should execute.

STOCRS defines which nodes are structurally resolvable and what supported values follow from declared deterministic rules.

Operational scheduling may still exist independently.

---

# **SECTION J — Scope and Non-Claims**

## **J1. What does STOCRS not claim?**

STOCRS does not claim:

- universal order independence
- universal time independence
- universal convergence of arbitrary distributed protocols
- elimination of communication
- elimination of physical execution
- elimination of operational coordination
- automatic completion from bounded sharing
- production safety certification
- formal technical-standard recognition

---

## **J2. Does STOCRS guarantee performance improvements?**

No.

The reference implementation focuses on structural resolution and correctness properties, not performance optimization.

---

## **J3. Is STOCRS production-ready?**

No production-readiness claim is made.

The repository provides a public reference implementation.

Production use requires additional engineering, security review, operational design, and independent validation.

---

## **J4. Does STOCRS eliminate clocks everywhere?**

No.

Clocks may remain useful or necessary for:

- logging
- monitoring
- scheduling
- expiration
- timeout handling
- user-facing operations
- physical coordination

STOCRS only demonstrates that the tested supported computational result is not selected by clock values.

---

## **J5. Does STOCRS eliminate ordering everywhere?**

No.

Many systems and computations inherently depend on order.

STOCRS demonstrates arrival-order independence only for the declared reference cases where the same relevant complete compatible structure and deterministic rules are eventually available.

---

# **SECTION K — Architectural Perspective**

A coordination-heavy system may use:

`time + order + synchronization -> operational agreement`

The STOCRS reference model asks whether some computational decisions can instead use:

`declared structure + frozen rules -> supported result`

This is a shift in **resolution authority**.

It is not a claim that execution, communication, transport, or operational coordination disappear.

---

# **SECTION L — Why This Matters**

## **L1. Why is this important?**

Because some systems may benefit from separating:

- operational history
- transport order
- clock state
- evidence multiplicity

from:

- computational authority

STOCRS demonstrates one bounded way to make that separation explicit.

---

## **L2. What is the broader implication?**

Where the required structure is complete, compatible, and governed by deterministic rules:

- a global clock may not be needed as computational authority
- arrival order may not be needed as computational authority
- continuous synchronization may not be needed as computational authority

This may support research into deterministic, replay-verifiable, conflict-aware structural systems.

---

# ⭐ **ONE-LINE SUMMARY**

**STOCRS is a bounded deterministic structural computation reference model in which incomplete structure remains unresolved, conflicting claims cannot override declared computation, and systems evaluating the same complete compatible structure under the same frozen rules produce the same supported result without using time, arrival order, continuous synchronization, or claim majority as computational authority.**
