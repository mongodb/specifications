# Analysis: benchmarking

## Missing Tests

- [ ] Percentile calculation (Nearest Rank method: `i = int(N * p / 100) - 1`) — no reference dataset or expected output
    to verify implementations
- [ ] Median score formula: `score = task_size_MB / median_wall_clock_time` — no reference implementation to verify
    correctness
- [ ] Iteration criteria: "at least 1 min cumulative; stop after 100 iterations or 5 min, whichever is shorter" —
    ambiguous stopping conditions (see Inconsistencies)
- [ ] GridFS upload/download with file I/O — no test for file integrity after upload (silent data corruption)
- [ ] Composite score calculation (BSONBench, SingleBench, MultiBench, ParallelBench, ReadBench, WriteBench,
    DriverBench) — no reference implementation
- [ ] Timer source is wall-clock, not CPU time — no test for this
- [ ] Concurrency semantics for Parallel tests — no specification of a comparable metric across languages

## Ambiguities

- **"Language-appropriate document types"**: Repeated throughout; no definition of what constitutes an appropriate type
    or how to handle BSON/language type impedance mismatches (e.g., Python `Decimal128` vs `float`).
- **Benchmark server configuration (TBD)**: Instance size, auth, journaling, WT compression — critical configuration
    left unspecified even though the spec is "Accepted."
- **JIT warm-up**: "Languages with JIT compilers MAY do warm-up iterations" — optional, encouraged, or required? How
    many iterations? Creates an unfair cross-language comparison if no limits are set.
- **Write concern hardcoded to `w:1`**: Never justified; may not reflect real-world workloads.
- **Dataset versioning**: No mechanism to detect or enforce version compatibility between v1 and v2 benchmarks.

## Inconsistencies

- **Stopping conditions conflict**: "Loop at least 1 minute cumulative" (SHOULD) vs. "stop after 100 iterations or 5
    minutes, whichever is shorter" — if 1 minute is reached at iteration 50, should the loop continue to 100? No
    conflict resolution is provided.
- **Dataset size vs wall-clock time**: Setup/teardown are included in dataset size calculation but the spec does not
    clarify whether setup/teardown time is included in the wall-clock measurement. If excluded, the score formula is
    incorrect.
- **"Run Command" excluded from DriverBench**: Listed in the spec but does not contribute to any composite score
    (SingleBench, ReadBench, WriteBench, or DriverBench). Why include it?
- **BSONBench excluded from DriverBench** (line 709): Benchmarked but not included in the overall score. Metrics are
    published but do not influence the comparison — seems contradictory.

## Notes

- Spec has multiple **TBD sections**: Benchmark Client (line 715), Benchmark Server (line 720), Score Server (line 726).
    The spec is marked "Accepted" but is incomplete.
- No reference implementation or sample results are provided to validate driver implementations.
- Language-specific optimizations (JIT warm-up, concurrency model) are allowed without limits, making cross-driver
    comparisons questionable.
- `data/` directory exists with datasets but the spec does not specify how to download or verify them.
