# Phase 0 Deterministic Substrate Contract

State: `NOT_RUN`

Phase 0 exists to prove that N64 ROM Forge can identify a known-clean input, freeze the exact source/toolchain state, rebuild a reference target deterministically, compare relevant objects, verify N64 header checksums, and emit receipts.

This scaffold does **not** authorize or claim that any of those ROM-facing actions have run.

## Gates

1. Input is user-supplied, read-only, outside GitHub/Drive/Notion, and matches the adapter's accepted hash.
2. Byte order is detected before interpretation.
3. CIC/IPL3 is evidence-backed. Unknown is preferable to invention.
4. Upstream commits and object-diff binary digest match `config/upstreams.lock.yaml`.
5. Base-image digest, package versions, executable hashes, and environment digest are resolved before build.
6. Deterministic build and object-oracle execution run with network disabled.
7. Reference ROM hash and object/diff smoke tests pass before any modification lane.
8. CRC1/CRC2 provenance is recorded and no checksum-repair claim is made without deterministic verification.
9. No ROM, ROM-derived asset, build output, or commercial payload is committed.
10. Execution receipts are immutable evidence; chat text is not execution truth.

## Lane separation

- `vanilla_reference`: exact `n64decomp/sm64` US reference lane.
- `hackersm64`: future modification lane. Its pinned upstream requires US and JP baseroms. It remains blocked until both read-only inputs are fingerprinted under a separately authorized run.
