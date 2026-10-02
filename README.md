# N64 ROM Forge

Evidence-governed, game-independent Nintendo 64 reverse-engineering and mod-development workbench.

Current state: the original deterministic read-only intake substrate plus a hardware-validated reverse-engineering tool/runtime layer.

This repository contains source, contracts, adapter metadata, reproducible emulator build/runtime metadata, portable analysis tools, and ROM knowledge records. It does **not** contain commercial ROMs, ROM-derived assets, generated emulator binaries, or build outputs.

## What is currently working

- read-only ROM fingerprinting, byte-order normalization, adapter resolution, CIC/checksum evidence, and JSON receipts
- portable N64 structural profilers and table/resource detectors
- VR4300/MIPS III big-endian disassembly with explicit delay-slot metadata
- JAL/JALR XREF analysis with bounded register/stack propagation and provenance
- local control-flow slices around recovered callsites
- strict compression probing and DKR RZIP decoding
- nested LUT/payload unpacking
- debugger register-trace parsing
- Mupen64Plus 2.6.0 debugger build/runtime contract for Windows x64
- timed debugger probe plans with durable receipts
- experiment-envelope contract for hypothesis/discriminator/evidence/change workflows
## Hardware-validated emulator runtime

The validated observer is Mupen64Plus 2.6.0 built with `DEBUGGER=1` and run in cached-interpreter mode:

```text
--debug --emumode 1
```

Exact upstream pins, build instructions, runtime hashes, plugin choices, and the stable timed probe runner live in:

```text
runtime/mupen64plus/
```

Generated third-party emulator binaries remain external. The repo records how to reproduce and identify the exact runtime instead of checking in opaque build products.

## Tool layout

```text
tools/generic/   reusable ROM-independent analyzers
tools/dkr/       Diddy Kong Racing-specific parsers/adjudicators
runtime/         reproducible emulator/debugger runtime contracts
knowledge/       promoted common and ROM-specific findings
schemas/         receipts, adapters, and experiment contracts
docs/workflows/  evidence, experiment, and promotion workflows
```
## Diddy Kong Racing Rev A

The current DKR lane is based on a locally verified USA Rev A ROM identity. Only hashes and derived semantic knowledge are committed.

Promoted findings include:

- 50-section top-level relative asset LUT
- DKR RZIP wrapper and 1,052 validated nested decodes
- level-model, object-model, animation, object-definition, and level-object-map banks
- 138 object-map slots with 9,426 parsed placements
- object IDs joined through definitions into object-model IDs
- native runtime object constructor and level selector addresses
- successful single-level native direct boot into Ancient Lake using the game's own transition path

See `knowledge/dkr/`.

The generalized named-level launcher is **not** promoted yet because its same-process stack-relative debugger control still needs final validation.

## Evidence workflow

Local ROM/runtime evidence outranks web/common knowledge. Findings move through:

```text
Observation -> Hypothesis -> Discriminator -> Evidence
-> Change Authorization -> Change -> Validation/Replay
-> Finding -> Promotion
```
External search is used as a narrowed hypothesis source after local evidence stalls, not as a substitute for ROM/runtime validation. Infrastructure failures do not count as ROM hypothesis failures.

See `docs/workflows/EVIDENCE_WORKFLOW.md` and `schemas/experiments/EXPERIMENT_ENVELOPE.schema.json`.

MIPS analysis behavior and limits are documented in `docs/workflows/MIPS_ANALYSIS.md`.

## Read-only ROM wrapper

```text
ROM path -> fingerprint -> byte-order normalization
-> Game Adapter resolution -> CIC/checksum evidence -> JSON receipt
```

CLI:

```bash
n64rf inspect <rom-path> [--adapter auto|<id>] [--receipt receipt.json]
n64rf verify <rom-path> --adapter <id> [--receipt receipt.json]
n64rf adapters list
n64rf adapters show <id>
```

GoldenEye 007 US remains the authoritative external regression fixture for the wrapper lane. DKR knowledge is intentionally not registered as checksum-PASS until its exact CIC/checksum evidence is independently admitted by the wrapper.

## Safety and provenance boundary

Original ROMs remain external, read-only inputs. Never commit or mirror ROM bytes or extracted commercial assets. Keep exact hashes, source pins, contracts, code, semantic findings, and metadata-only receipts.

A failed or reverted implementation may still leave a valid finding. Preserve evidence and anti-patterns even when a patch is discarded.
