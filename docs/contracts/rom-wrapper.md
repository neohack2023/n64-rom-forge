# Read-Only ROM Wrapper Contract

State: `IMPLEMENTED_ON_INTEGRATION_BRANCH`

The wrapper is orchestration, not a second ROM-analysis implementation.

## Backend ownership

- `n64rf.rom_inspector`: source hashing, byte-order detection, canonical in-memory view, header/IPL3 fingerprints.
- `n64rf.adapters`: per-game identity and canonicalization rules.
- `n64rf.checksum`: CIC evidence and CRC1/CRC2 verification.
- `n64rf.receipts`: typed evidence structures.
- `n64rf.wrapper`: composes the backend and verifies source integrity before/after.
- `n64rf.cli`: filesystem/user interface only.

## Read-only invariant

`read-only` means wrapper-controlled I/O, not merely POSIX permission bits. The wrapper:

1. opens ROM input with `rb` only;
2. records filesystem mode/writability as evidence;
3. hashes the source before interpretation;
4. canonicalizes only in memory;
5. hashes the original source again before returning;
6. records failure if the source fingerprint changes;
7. refuses to write a receipt over the ROM path.

Immutable mounts remain preferred for later CI and deterministic build execution.

## Adapter rules

Adapters identify canonical game inputs, not arbitrary filenames. A candidate may be:

- `full-image`: normalized input must have the exact canonical size/hash;
- `canonical-prefix`: an evidence-backed prefix may identify the canonical target while trailing bytes are separately hashed/classified.

A canonical-prefix rule never authorizes mutation of the original source.

## Fixture 01: GoldenEye 007 US

The external 16 MiB `v64` fixture normalizes to a 12 MiB canonical prefix matching adapter `goldeneye-007-us` and a 4 MiB noncanonical tail. The regression test is activated only when `N64RF_GOLDENEYE_FIXTURE` points to the user-supplied ROM. No ROM bytes are stored in the repository.

## Success gate

The wrapper returns success only when all are true:

- before/after source fingerprints match;
- exactly one Game Adapter matches;
- checksum verification is `PASS` for a supported evidence-backed CIC.

Unknown/ambiguous identity or unsupported CIC verification fails closed.

This contract does not authorize asset extraction, decompilation, build execution, modification, emulator validation, hardware validation, patch generation, or a merge to `main`.
