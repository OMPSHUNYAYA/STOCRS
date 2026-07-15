# ⭐ **STOCRS — Quickstart**

**Shunyaya Timeless Computation — Reference Implementation**

**Deterministic • Structure-Driven • Explicit Incompleteness • Conflict-Aware • Replay-Verifiable**

---

## ⚡ **30-Second Demonstration**

From the repository root, run:

```text
python demo\stocrs_canonical_demo_v1_2.py --seed 101 --systems 5
```

### **What to observe**

- systems begin with different incomplete fragments
- intermediate phases remain unresolved
- local clock values differ
- time is not used as computational authority
- the final complete compatible structure produces the same supported result across all systems
- the conflict story reports successful stable, conflict, and recovery behavior

### **Expected final lines**

```text
Final Complete OK: YES
Final Match OK: YES
Final Node Count: 20
Final E1: 202

Stable OK: YES
Conflict OK: YES
Recovery OK: YES
```

### **Reference relation**

`same complete compatible structure + same frozen rules -> same supported structural result`

---

## 🧭 **Core Principle**

STOCRS models computation as deterministic structural resolution.

It does not treat these as computational authority in the declared reference cases:

- wall-clock time
- timestamps
- fragment arrival order
- continuous synchronization
- claim multiplicity

Instead:

`declared structure + frozen rules -> computational authority`

---

## 🔍 **What STOCRS Models**

STOCRS represents computation as a dependency-governed structure.

Each node:

- has declared dependencies
- becomes resolvable only when those dependencies are available
- is computed by its declared deterministic rule
- may remain unresolved while structure is incomplete
- may be blocked by conflicting or structure-incompatible claims

### **Example dependency fragment**

```text
E1 -> D1, D2
D1 -> C1, C2
D2 -> C2, C3
```

Resolution proceeds through structural readiness rather than fragment arrival order.

---

## 🚫 **What STOCRS Does NOT Claim**

STOCRS does not claim that:

- every computation can ignore time or order
- partial sharing alone guarantees complete dissemination
- communication is unnecessary
- execution, transport, persistence, or operational coordination disappear
- it replaces consensus protocols or distributed databases
- the current reference implementation is a production safety certification

The current claim is narrower:

**within the declared reference model, the supported computational result is determined by declared structure and frozen rules rather than by time, arrival order, or claim multiplicity.**

---

## ✅ **What the Current Reference Implementation Demonstrates**

- different incomplete initial fragments
- explicit unresolved intermediate states
- different fragment orders
- different local clock values
- bounded intermediate sharing
- deterministic final agreement after explicit complete compatible structure becomes available
- conflict abstention at the affected node
- dependent unresolved state when a required dependency is conflicted
- rejection of claim majority as computational authority
- recovery after conflicting evidence is corrected or removed
- replay and SHA-256 verification

---

## ⚙️ **Minimum Requirements**

- Python 3.9+
- standard library only
- no external Python dependencies
- canonical and runtime demonstrations run fully offline

The GitHub Actions workflow currently uses Python 3.10.

---

## 📁 **Repository Structure**

```text
STOCRS/

├── .github
│   └── workflows
│       └── verify.yml
│
├── README.md
├── LICENSE
│
├── demo
│   ├── stocrs_poc_demo.py
│   ├── stocrs_canonical_demo_v1_2.py
│   └── stocrs_reconciliation_demo_v1_1.py
│
├── runtime
│   └── stocrs_engine_v1_1.py
│
├── historical_scripts
│   ├── stocrs_v1_demo.py
│   ├── stocrs_v2_fragmented_demo.py
│   ├── stocrs_v2_fragmented_stress.py
│   ├── stocrs_v3_isolation_demo.py
│   ├── stocrs_v4_large_graph_demo.py
│   ├── stocrs_v5_multi_system_demo.py
│   ├── stocrs_v6_adversarial_demo.py
│   ├── stocrs_v7_conflict_demo.py
│   ├── stocrs_v8_partial_sharing_demo.py
│   └── stocrs_v9_bounded_sharing_demo.py
│
├── reference_outputs
│   ├── reconciliation_demo_v1_1.json
│   ├── reference_output.json
│   ├── reference_run.txt
│   ├── stocrs_canonical_demo_v1.json
│   └── stocrs_conflict_demo_v1.json
│
├── docs
│   ├── STOCRS.png
│   ├── Shunyaya-Structural-Paradigm.png
│   ├── FAQ.md
│   ├── Quickstart.md
│   ├── Validation_Ledger.md
│   └── Convergence-Proof.md
│
└── VERIFY
    ├── FREEZE_DEMO_SHA256.txt
    ├── FREEZE_REFERENCE_OUTPUTS_SHA256.txt
    ├── FREEZE_RUNTIME_SHA256.txt
    ├── verify_all.bat
    ├── VERIFY_EXPECTED_RESULTS.txt
    └── VERIFY_INSTRUCTIONS.txt
```

The previous `STOCRS_v1.8.pdf` and `Concept-Flyer_STOCRS_v1.8.pdf` are not part of the current documentation set.

---

## 🧠 **Folder Roles**

- `demo/` — current demonstrations, including the canonical and reconciliation cases
- `runtime/` — current reusable structural runtime
- `reference_outputs/` — frozen reference artifacts used for verification
- `VERIFY/` — SHA-256 freeze records, expected properties, instructions, and the Windows verifier
- `historical_scripts/` — preserved implementation evolution
- `docs/` — current supporting documentation and diagrams
- `.github/workflows/` — automated repository verification

The POC demo is illustrative.  
The canonical demo, current runtime, frozen reference outputs, and verification bundle form the primary verification path.

---

## ⚡ **Run the Canonical Demo**

```text
python demo\stocrs_canonical_demo_v1_2.py --seed 101 --systems 5
```

### **Expected output**

```text
No GPS: YES
No NTP: YES
No Internet: YES
Time Used for Correctness: NO

Phase 1 Diversity OK: YES
Phase 1 Incomplete OK: YES
Phase 2 Bounded OK: YES
Phase 3 Bounded OK: YES
Phase 4 Bounded OK: YES

Phase 1 Unresolved Exists: YES
Phase 2 Unresolved Exists: YES
Phase 3 Unresolved Exists: YES
Phase 4 Unresolved Exists: YES

Final Complete OK: YES
Final Match OK: YES
Final Node Count: 20
Final E1: 202

Stable OK: YES
Conflict OK: YES
Recovery OK: YES
```

The current canonical certificate is:

```text
150c3ca5135af3320929a4fc2a92cc39001d5b3f49a9ce972bcccc49c1c55f36
```

The current conflict-story certificate is:

```text
8cb9667dfc12e6a09ea0728e927b3f19609eee0eac00159d062e2980a67bd2b9
```

---

## ⚖️ **Run the Runtime Conflict Demonstration**

```text
python runtime\stocrs_engine_v1_1.py --conflict-demo
```

Expected behavior:

### **Stable Run**

```text
X1 = 2
X2 = 3
A1 = 5
```

### **Conflict Run**

For:

`X1 -> [2, 9]`

the runtime records:

`multi_value_conflict`

`X1` does not resolve from the conflicting claims.

Because `A1` depends on `X1`, `A1` remains unresolved.

### **Recovery Run**

After conflicting evidence is corrected or removed:

```text
X1 = 2
X2 = 3
A1 = 5
```

The current runtime conflict certificate is:

```text
3c9ce1ef545e1dd573dcebcd90945a81beb42636d535633769a950df2363eadc
```

---

## 🛡 **Conflict Authority Rule**

The runtime follows this rule:

`claim multiplicity != structural authority`

Therefore:

- `[2, 2]` may corroborate the declared structural value `2`
- `[2, 9]` is a multi-value conflict
- `[9, 9]` cannot override a structurally computed value of `2`
- `[9, 9, 2]` cannot become authoritative through majority support

Declared computation remains authoritative within the reference model.

---

## 🔁 **Determinism Check**

Run the canonical demo again with the same declared parameters:

```text
python demo\stocrs_canonical_demo_v1_2.py --seed 101 --systems 5
```

Expected:

- the same reported structural result
- the same canonical certificate
- the same conflict-story certificate

For machine-readable reproduction:

```text
python demo\stocrs_canonical_demo_v1_2.py --seed 101 --systems 5 --json
```

The canonical JSON no longer contains elapsed runtime data, allowing exact comparison with the frozen canonical reference artifact.

---

## 💾 **Reference Artifacts**

The current frozen reference artifacts are:

- `reference_outputs\reference_output.json`
- `reference_outputs\reference_run.txt`
- `reference_outputs\reconciliation_demo_v1_1.json`
- `reference_outputs\stocrs_canonical_demo_v1.json`
- `reference_outputs\stocrs_conflict_demo_v1.json`

`reference_output.json` and `stocrs_canonical_demo_v1.json` contain the same canonical JSON reference content.

The reconciliation artifact retains its recorded elapsed runtime field, so reconciliation verification compares the declared semantic fields and certificate rather than requiring exact byte-for-byte reproduction.

---

## 🔐 **Deterministic Certificates**

The canonical demo computes its certificate from a deterministic certificate payload.

The certificate binds the declared reference-case structural data included in that payload.

Code and artifact identity are verified separately through the SHA-256 freeze files in `VERIFY/`.

This distinction is important:

`certificate -> deterministic declared result payload`

`FREEZE SHA256 -> exact file identity`

---

## 🔬 **Canonical Phase Model**

### **1. Initial fragments**

Systems begin with different incomplete structural views.

Expected:

`unresolved exists`

### **2. Bounded intermediate sharing**

Systems gain more structure but remain incomplete.

Expected:

`unresolved exists`

### **3. Explicit complete structure**

Each system receives the complete declared node set.

Expected:

`complete`

### **4. Final comparison**

All systems evaluate the same complete compatible structure under the same frozen rules.

Expected:

`match`

The bounded sharing phases demonstrate incomplete structural progression.

They do not by themselves prove that bounded sharing guarantees eventual complete dissemination.

---

## 🔁 **Reconciliation Demonstration**

Run:

```text
python demo\stocrs_reconciliation_demo_v1_1.py --seed 101
```

The declared reference case demonstrates:

- 4 systems
- different incomplete starting fragments
- no logs used by the model
- no timestamps used as computational authority
- no arrival-order requirement for the tested final result
- explicit complete structure in the completion phase
- identical final supported values across the 4 systems

Expected final values:

```text
ACC1_FINAL = 120
ACC2_FINAL = 40
ACC3_FINAL = 80
TOTAL_BALANCE = 240
```

---

## ✅ **Complete Verification**

### **Windows**

From the repository root:

```text
VERIFY\verify_all.bat
```

The verifier checks:

- all current demo hashes
- current runtime hash
- all frozen reference-output hashes
- exact canonical JSON reproduction
- reconciliation semantic agreement
- conflict-authority regression behavior

Expected final status:

```text
VERIFY RESULT: PASS
Deterministic reproduction confirmed within the declared reference cases.
```

---

## 🔐 **Frozen SHA-256 Verification**

The freeze records are:

```text
VERIFY\FREEZE_DEMO_SHA256.txt
VERIFY\FREEZE_RUNTIME_SHA256.txt
VERIFY\FREEZE_REFERENCE_OUTPUTS_SHA256.txt
```

They bind the current public files used by the verification path.

The repository workflow at:

```text
.github\workflows\verify.yml
```

performs automated verification on pushes and pull requests to `main`.

---

## 📌 **What STOCRS Demonstrates**

Within the declared reference cases:

- incomplete structure can remain explicitly unresolved
- arrival-order differences do not alter the tested final result once the same complete compatible structure is available
- divergent local clock values are not used as computational authority
- conflicting claim multiplicity cannot override declared structure
- structurally incompatible claims do not force an incorrect dependent result
- corrected or removed conflicting evidence can allow resolution to proceed again
- deterministic reference artifacts can be replayed and hash-verified

---

## ⚠️ **Claim Boundary**

The reference implementation demonstrates a bounded structural computation model.

It does not establish that:

- all computations are order-independent
- all distributed systems can eliminate coordination
- all partial-information protocols converge automatically
- communication or execution infrastructure is unnecessary

The supported relation is:

`same complete compatible structure + same frozen rules -> same supported structural result`

---

## 🔁 **Structural Convergence**

For the canonical complete compatible states:

`same structure + same rules -> same result`

Different fragment orders may lead to different intermediate partial states.

Once the same complete compatible structure is available, the tested systems produce the same supported final result.

This is convergence by structural equivalence in the declared reference case, not a universal guarantee about arbitrary distributed protocols.

For the formal argument and scope boundary, see:

`docs\Convergence-Proof.md`

---

# ⭐ **One-Line Summary**

**STOCRS demonstrates, within its declared reference cases, that systems can begin with different incomplete fragments and different local clock values, remain unresolved while structure is incomplete, reject conflicting claims as computational authority, and produce the same deterministic result once the same complete compatible structure is available under the same frozen rules.**
