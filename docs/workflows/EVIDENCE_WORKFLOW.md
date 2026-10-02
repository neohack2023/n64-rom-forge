# Evidence-first reverse-engineering workflow

Authority order for ROM semantics:

1. exact ROM identity and local bytes
2. deterministic static analysis
3. emulator/runtime witness
4. reproducible experiment receipt
5. external source/decomp correlation
6. general web knowledge

External knowledge is a hypothesis source, not authority, until local evidence agrees.

Experiment lifecycle:
`Observation -> Hypothesis -> Discriminator -> Evidence -> Change Authorization -> Change -> Validation/Replay -> Finding -> Promotion`

A failed or reverted change may still leave a valid finding. Findings survive implementation state when their evidence remains valid.

Search policy used by the N64 lab:
- keep search dormant while local discriminators are producing information
- after three evidence-bearing hypothesis failures on the same unresolved branch, search narrowly using accumulated local evidence
- infrastructure/tool failures do not count as hypothesis strikes
- a new successful discriminator resets the strike count

Never weaken authority/resource/context guards to make an experiment pass.
