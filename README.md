# N64 ROM Forge

Evidence-governed, game-independent Nintendo 64 reverse-engineering and mod-development workbench.

Current governed substrate: `N64RF-PHASE0-DETERMINISTIC-SUBSTRATE-01`.

This repository contains source, contracts, adapter metadata, and receipts only. It does not contain commercial ROMs, ROM-derived assets, build outputs, or patches.

## Read-only ROM wrapper

The Phase 0 substrate now exposes a real read-only intake backend:

```text
ROM path -> fingerprint -> byte-order normalization -> Game Adapter resolution -> CIC/checksum evidence -> JSON receipt
```

CLI:

```bash
n64rf inspect <rom-path> [--adapter auto|<id>] [--receipt receipt.json]
n64rf verify <rom-path> --adapter <id> [--receipt receipt.json]
n64rf adapters list
n64rf adapters show <id>
```

The wrapper opens source ROMs with `rb`, hashes before and after inspection, never persists canonicalized/trimmed ROM bytes, and fails its success gate if source integrity, adapter identity, or checksum verification fails.

### Regression fixture 01

GoldenEye 007 US is the first real fixture. Only expected fingerprints are committed. The ROM remains external to the repository.

- observed source representation: 16 MiB `v64`
- raw SHA-1: `cb9bbf8fbcb5b204f56ec2d43fc0e555ecfd0927`
- canonical first 12 MiB SHA-1: `abe01e4aeb033b6c0836819f549c791b26cfde83`
- adapter: `goldeneye-007-us`
- CIC: `CIC-NUS-6102`
- CRC1/CRC2: `0xDCBC50D1 / 0x09FD1AA3`
- trailing 4 MiB is recorded as noncanonical evidence, never silently trimmed from the source object

To run the external fixture regression locally:

```bash
N64RF_GOLDENEYE_FIXTURE=/path/to/007-GoldenEye.v64 \
  python -m unittest discover -s tests -v
```

## Frozen execution facts

- Repository baseline: `neohack2023/n64-rom-forge@0476eab45e725a2dbe3c93af0866588b3e0e6c03`
- Phase 0 substrate commit: `8cac404f44dd6e3793b98e56ac4ce93ed061cb58`
- Vanilla reference: `n64decomp/sm64@9921382a68bb0c865e5e45eb594d9c64db59b1af`
- Modification target: `HackerN64/HackerSM64@3f1f7f41beac4ff0287bcb5f919efb52856ec27b`
- Object oracle tool: `encounter/objdiff@v3.8.1`
- Phase 0 build execution state: `NOT_RUN`

## Safety invariant

Original ROMs remain external, read-only inputs. Never commit or mirror ROM bytes into GitHub, Notion, or the N64RF Drive branch. Only fingerprints, contracts, source pins, code, and metadata-only receipts belong there.
