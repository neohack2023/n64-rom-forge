# N64 Port Experiment Contract

Every causal port/debug slice must produce one experiment envelope before a semantic patch is accepted.

1. HYPOTHESIS — state one falsifiable explanation and competing alternatives.
2. DISCRIMINATOR — define a probe, toggle, replay, trace, or differential with different expected outcomes for true vs false.
3. PATCH — remains blocked until discriminator evidence is recorded as PASS or otherwise explicitly adjudicated.
4. FINDING — records what was learned independently of whether the patch survives.

Rules:
- A passing build is not by itself a discriminator for a behavioral hypothesis.
- Native playtest may be evidence, but its observation and target state must be recorded.
- Reverted patches do not delete findings.
- Unattributed fixes are recorded as UNRESOLVED_CAUSALITY, not promoted as causal patterns.
- Failed hypotheses become anti-pattern/replay candidates.
- Findings may feed ROM-specific knowledge immediately, but general N64 promotion still follows KNOWLEDGE/PROMOTION_POLICY.md.
- Existing runtime-contract adjudication remains authoritative for runtime promotion.
