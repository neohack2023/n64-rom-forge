# N64 Reverse-Engineering Continuity Handoff — 2026-10-03

Status: DURABLE_CONTEXT_HANDOFF
Scope: n64-rom-research + n64-rom-forge
Purpose: preserve the evidence, methods, implementation state, and unresolved gates learned in the 2026-09-24 through 2026-10-03 N64 reverse-engineering sessions so a future session can resume without reconstructing chat history.

## 1. Authority and operating rules

Authority order for N64 semantics:
1. Exact local ROM identity and bytes.
2. Deterministic static analysis.
3. Emulator/runtime witness.
4. Reproducible experiment receipt.
5. External source/decomp correlation.
6. General web knowledge.

External knowledge is a hypothesis source, not authority, until local ROM/runtime evidence agrees.

Search policy:
- Keep web search dormant while local discriminators are still producing information.
- After three evidence-bearing hypothesis failures on the same unresolved branch, search narrowly using the accumulated local evidence.
- Infrastructure/tool failures do not count as hypothesis strikes.
- A successful new discriminator resets the strike count.

Experiment lifecycle:
`Observation -> Hypothesis -> Discriminator -> Evidence -> Change Authorization -> Change -> Validation/Replay -> Finding -> Adjudication/Promotion`

A finding can survive a failed or reverted implementation if the evidence supporting the finding remains valid.

Never weaken Host02 authority, resource, ownership, or context guards to make an experiment pass.

## 2. Canonical Host02 surfaces

Research workspace:
`C:\AIOS\04_WORKSPACES\EMULATION\N64\WORKSPACES\N64_ROM_REVERSE_ENGINEERING_01`

Port/experiment workspace:
`C:\AIOS\04_WORKSPACES\EMULATION\N64\WORKSPACES\N64_CROSS_PLATFORM_PORT_LAB_01`

Shared emulator runtime:
`C:\AIOS\01_TOOLS\N64_EMULATION_RUNTIME_01`

Primary Mupen runtime:
`C:\AIOS\01_TOOLS\N64_EMULATION_RUNTIME_01\emulators\mupen64plus-2.6.0-debug-current-ui`

N64 forge repo working tree:
`C:\AIOS\99_STAGING\n64-rom-forge-sync`

Repo authority:
`neohack2023/n64-rom-forge`, branch `main`.

WSL asset:
`C:\AIOS\01_TOOLS\WSL_RUNTIME_01`
Distro: `AIOS-Ubuntu-22.04`.
Current usable state: WSL1. WSL2 is blocked only by firmware virtualization/VT-x being disabled; no reinstall is required to upgrade later.

Tool lookup is centralized in the shared N64 emulator runtime `TOOL_INDEX.json`; generic tools should live in shared/runtime or repo generic-tool locations, not consumer workspaces.

## 3. Emulator/runtime model

Primary runtime is Mupen64Plus 2.6.0 with the locally validated debugger-enabled core/UI. Normal playable validation has used cached interpreter, Rice video, SDL audio/input, and HLE RSP. CXD4 RSP and Glide64mk2 are available as comparison lanes.

Runtime evidence rules:
- A breakpoint command is not proof that the breakpoint fired.
- Record intended breakpoint, actual hit, registers/memory after the hit, and timing.
- Timing/probe failures are invalid probes, not ROM-hypothesis failures.
- Audio-active execution is not visual acceptance.
- A ROM that boots CPU/audio but shows black video is not automatically corrupt.

Host02 black-video incident lesson, 2026-10-03:
- Developer Lab, vanilla NON_MATCHING control, original Rev A, and known-good All-Tracks were observed with audio/CPU active while video was black during the incident.
- Rice configuration lookup was confounded by working directory. The emulator runtime contains `RiceVideoLinux.ini`, `InputAutoCfg.ini`, and `mupen64plus.ini`; launch CWD therefore matters.
- A later recovery record reports successful rendering again after stale/concurrent emulator process cleanup and clean single-instance launches, including Developer Lab rendering through splash/attract. Root cause remains unconfirmed because process concurrency and CWD changed together.
- Do not promote “multiple Mupen instances lock video” as canon. It is only a remaining hypothesis.
- Future launcher work should explicitly set emulator CWD, record PID/owner/config/ROM hash, and detect stale instances before acceptance runs.

Incident evidence:
`reports/HOST02_N64_VIDEO_BLACK_AUDIO_ACTIVE_01.md`

## 4. Generic N64 reverse-engineering knowledge

### ROM identity
Pin revision, byte order, file size, MD5/SHA-1/SHA-256, internal title, game code, version byte, entrypoint, and CIC before assigning semantics. `.z64`, `.v64`, and `.n64` are representations, not interchangeable evidence unless normalization is explicit.

### Resource discovery
Do not assume one asset-table family across games. DKR disproved the Rugrats-style reusable absolute start/end-table hypothesis and instead exposed a top-level relative LUT plus nested adjacent LUT/payload banks.

Compression detectors must require strong invariants. Random binary can accidentally terminate as a tiny raw-DEFLATE stream. Require wrapper signature/structure, declared-size agreement, EOF, and padding constraints before promoting a compression family.

### MIPS analysis
N64 CPU code is MIPS with branch delay slots. The instruction after a branch/jump/call executes before transfer. Argument recovery that ignores delay slots is invalid.

The evolved shared MIPS tooling supports:
- J/JAL/JR/JALR
- BEQ/BNE/BLEZ/BGTZ plus likely variants
- REGIMM BLTZ/BGEZ/likely/link variants
- 32-bit integer ops
- DADD/DADDU/DSUB/DSUBU and DADDI/DADDIU
- 64-bit shifts including *32 and variable forms
- LWU, LDL/LDR, LD, SDL/SDR, SD, LLD/SCD
- common loads/stores
- delay-slot metadata
- LUI + ADDIU/DADDIU and LUI + logical-immediate propagation
- zero-register moves
- stack-frame adjustment
- SW/SD save and LW/LWU/LD reload
- caller-saved clobber across intervening calls
- delay-slot writes before callee argument observation
- concrete JALR target recovery when numeric provenance exists
- bounded local CFG for calls/branches/fallthrough/delay/return

Fail-closed limits:
- analysis is not globally path-sensitive
- unknown global-memory loads remain unknown
- symbolic JALR targets are not admitted as concrete
- overlays require the correct ROM and VRAM bases
- function-entry labels are only asserted when a recognizable stack frame/RA-save pattern supports them; otherwise use window-entry semantics

Repo implementation:
`tools/generic/mips_common.py`
`tools/generic/mips32_be_disasm_min.py`
`tools/generic/n64_mips_jal_xref.py`
`tests/test_mips_tools.py`
`docs/workflows/MIPS_ANALYSIS.md`

## 5. Current ROM coverage

Validated entrypoint/runtime or structural lanes exist for multiple local ROMs, including Ocarina of Time Rev A, Super Mario 64, Mario Kart 64, Star Fox 64, F-Zero X, Banjo-Kazooie, Pilotwings 64, GoldenEye, Conker, Perfect Dark, Rugrats, and Diddy Kong Racing.

Do not treat equal coverage as equal semantic depth. DKR currently has the richest N64 game-specific structural/runtime corpus. OoT has strong DMA/overlay/runtime correlation. Several others currently have entrypoint witnesses, decomp/recomp bridges, structural manifests, or narrower runtime probes rather than deep semantic maps.

## 6. Diddy Kong Racing US Rev A — canonical identity

Local target:
`Diddy Kong Racing (USA) (En,Fr) (Rev A).z64`

Identity:
- size: 12,582,912 bytes
- MD5: `b31f8cca50f31acc9b999ed5b779d6ed`
- SHA-1: `6d96743d46f8c0cd0edb0ec5600b003c89b93755`
- SHA-256: `7de1a8fb2a9558cfc3d9ad4497df698c1e89cf7095ac1531557df2af40ba8bcf`
- magic: `80371240`
- internal title: `Diddy Kong Racing`
- game code: `NDYE`
- version: 1
- entrypoint: `0x80100400`
- boot CRC32: `0B050EE0`
- CIC: X103 / 6103
- stock Goodname: `Diddy Kong Racing (U) (M2) (V1.1) [!]`
- original header CRC: `E402430D D2FCFC9D`

The local registry identifies this as canonical N64 source #10.

## 7. DKR structural map

Top-level asset LUT:
- ROM offset `0xED0E0`
- count 50
- payload base `0xED1B0`
- final boundary `0xA9FE20`
- ROM end `0xB8CFD0`

Nested adjacent LUT/payload pairs with high confidence:
`3->4, 5->6, 20->21, 22->23, 24->25, 26->27, 28->29, 31->32, 33->34, 40->41, 42->43`

Nested unpack found 2,498 subresources.

DKR compression wrapper was locally verified as:
`[LE u32 decoded size][0x09][raw DEFLATE][zero padding to 16-byte alignment]`

Nested compression results:
- 2,498 checked
- 1,071 candidates
- 1,052 valid
- 19 failed

Promoted roles:
- `26->27`: LEVEL_MODELS_TABLE -> LEVEL_MODELS, HIGH
- `28->29`: OBJECT_MODELS_TABLE -> OBJECT_MODELS, VERY_HIGH
- section `30`: ANIMATION_IDS, VERY_HIGH
- `31->32`: OBJECT_ANIMATIONS_TABLE -> OBJECT_ANIMATIONS, VERY_HIGH
- `33->34`: OBJECT_DEFINITIONS, with object ID as direct definition index

The initial generic gzip/zlib/raw-deflate hypotheses failed before the DKR wrapper was identified. Those evidence-bearing strikes justified the narrowed external search; after local wrapper validation the search strike counter reset.

## 8. DKR level-object graph

Sections `20->21` are level object maps:
- 138 slots
- 136 non-empty RZIP maps
- empty slots: 81 and 99
- 9,426 parsed placement records
- 85 unique object IDs
- record count range: 0 to 243, median 67

Runtime chain:
`level metadata -> map index -> table20 -> section21 -> RZIP -> placement records -> object constructor 0x8000EA54`

Important functions:
- initializer caller: `0x8006BCF0`
- initializer: `0x80024A30`
- map loader: `0x8000C8F8`
- table20 load: `0x8000CA18`
- section21 payload: `0x8000CAB0`
- inflate: `0x8000CAC0`
- per-record spawn: `0x8000CB10`
- general object constructor: `0x8000EA54`

Decoded placement format:
- map header is 16 bytes
- header +0 is BE u32 total record span
- records begin at +0x10
- object ID = `byte0 | ((byte1 & 0x80) << 1)`
- record length = `byte1 & 0x3F`
- BE signed XYZ at +2, +4, +6

Object definitions `33->34`:
- 304 definition slots
- object ID indexes definition directly
- +0x10 model-ID array pointer
- +0x14 model-ID array end
- +0x54 behavior selector
- +0x55 model count
- +0x60 label

All 85 level-used object IDs resolve into the definition bank. 177 distinct referenced object-model IDs resolve into `28->29` with no missing references.

## 9. DKR level headers, names, and map slots

`22->23` is the level-header table/payload:
- 65 records
- each record `0xC8` bytes

`24->25` contains 65 aligned localized level names.

Object-map slot fields:
- slot 0 = level header +`0xBA`, runtime loader `a1=0`
- slot 1 = level header +`0x36`, runtime loader `a1=1`

The loader `a1` selects runtime storage slot. It is not an object-constructor mode. Per-record object construction still receives `a1=1` in both layers.

Map ID ranges:
- slot0: 0..67
- slot1: 68..137

The complete 65-name level index is persisted in workspace/report evidence. Examples relevant to active experiments include Ancient Lake index 5, Horseshoe Gulch index 16, Trophy Race index 34, Future Fun Land index 35, and WizPig variants later in the table.

## 10. DKR direct-level boot experiment

Native level selector: `0x8006B490`.

Validated caller path:
- caller: `0x8006DD7C`
- JAL to selector: `0x8006DDC0`
- return: `0x8006DDC8`
- stable caller SP observed: `0x8011FC30`
- saved level argument observed at `0x8011FC50`

Changing only the saved level argument to 5 caused the native selector to receive level 5 and the downstream map loader to choose map 5 in slot 0 and map 73 in slot 1, matching Ancient Lake’s header metadata.

Finding: direct named-level transition is possible by changing the game’s own saved level argument before its native transition path. This experiment deliberately did not replace the game’s level loader.

State: `DIRECT_LEVEL_BOOT_01_PASS`.

Do not over-promote the unfinished generalized named-level launcher. The experiment finding is valid; the generalized implementation remains a separate gate.

## 11. Playable All-Tracks-Unlocked patch

A source/decomp correlation showed that the Tracks menu populates all real track IDs when the Adventure Two predicate succeeds. Local Rev A disassembly verified the corresponding call and branch.

Exact local site:
- predicate call: `0x8008F33C` -> `0x8009F1A4`
- branch: `0x8008F344`
- ROM offset: `0x8FF44`
- original word: `0x10400008`
- patched word: `0x00000000` (NOP)

The patch removes only the Tracks-menu conditional branch. It does not globally set Adventure Two unlocked.

Patched ROM identity:
- SHA-256: `52ee8add4245d16d3686a1801c58bea1aff2fc7cf25c12922a0f408aef34a130`
- repaired CRC1: `E402433D`
- repaired CRC2: `882FC584`

User acceptance: all tracks were visible and playable. This is end-to-end human confirmation, not only static proof.

Reusable repo implementation:
`patches/dkr/all_tracks_unlocked.py`
`patches/dkr/all_tracks_unlocked.json`

The patcher hard-gates the exact Rev A SHA-256, verifies the original word, writes the NOP, and recalculates CIC6103 CRC1/CRC2. ROM bytes are not distributed in the repo.

## 12. Native Developer Lab source-build lane

Design intent:
- visible Game Select option
- no hidden button chord
- no Tracks-menu piggyback
- native source-level menu so larger organized edits can be added cleanly

Pinned decomp source:
`DavidSM64/Diddy-Kong-Racing`
commit `a5eb080fa8f91b97d6f6495e0549ef7121ae7496`

V1 menu entries:
1. HORSESHOE GULCH
2. AUDIO / REVERB DEBUG ON/OFF
3. RETURN

Source delta is limited to five game files:
- `src/menu.h`
- `src/menu.c`
- `src/tracks.h`
- `src/tracks.c`
- `src/audio_spatial.h`

Current measured delta: 148 insertions / 6 deletions.

Build environment:
- `AIOS-Ubuntu-22.04` WSL1
- decomp setup toolchain built successfully
- US v80 extraction succeeded from the owned Rev A ROM
- `make REGION=us VERSION=v80 NON_MATCHING=1 -j2` succeeded
- final ELF linked
- native `.z64` emitted
- CIC6103 CRC repair succeeded

First build defect and correction:
- candidate used stale/nonexistent `gGameNumPlayers`
- canonical decomp symbol is `gNumberOfActivePlayers`
- correction compiled cleanly

Developer Lab built ROM:
`C:\AIOS\04_WORKSPACES\EMULATION\N64\ROMS\HACKS\Diddy Kong Racing (Rev A) - Developer Lab v1.z64`

Identity:
- SHA-256: `1307E2F002D0032E926F32401C369A7DA1D46BDDC2AD3E22B3B33A70191595BA`
- SHA-1: `251F5BA722185FA0BF2E274F2CA149FF15D193D9`
- CRC1: `C03EB9BC`
- CRC2: `D0D49425`

Build state is proven. Visual feature acceptance is a separate gate.

A later Host02 incident record reports that, after emulator runtime recovery, Developer Lab rendered the Rare splash and attract/title sequence. The Developer Lab menu itself and the audio/reverb debug behavior still require explicit visual/interactive acceptance before promotion as a finished feature.

Current repo working tree contains untracked `patches/dkr/dev_lab/`; do not accidentally commit unrelated temporary xref files with it. Promote the Developer Lab package only after the menu/feature acceptance gate passes.

## 13. Experiment contract now used by N64 work

N64 Port Lab is Reference Adapter 01 for the generic AIOS causal experiment model.

Current N64 envelope fields include:
- `experiment_id`
- `scope_key`
- `case_id`
- `created_utc`
- `state`
- hypothesis claim/observations/alternatives
- discriminator kind/procedure/expected-if-true/expected-if-false/evidence paths/result
- patch allowed/path-or-commit/state
- finding statement/confidence/survives-patch-revert/promotion-state

Schema family:
`n64.port_experiment_envelope.v1`

Important design rule: at the generic AIOS layer the mutation term should become `change`; N64 may retain `patch` as adapter language.

Experiment assets live under the Port Lab `experiment_contracts` directory. Findings should be promoted independently from implementation success/failure when evidence supports them.

## 14. Rugrats N64 lane

Rugrats is useful as a contrasting asset-family case, not as a template that DKR must follow.

Current useful state:
- generic local structural analysis has used ROM bytes plus captured RDRAM to look for compression streams, file-table geometry, pointer/address clusters, and ROM-to-RAM correlations
- runtime work previously stalled at title/menu under one N64 configuration, so gameplay-state capture was not treated as valid evidence
- the PS1 version was introduced as a comparative oracle to expose model/texture/material differences
- the PS2 reconstruction lane revealed that missing Tommy facial detail could come from renderer/material treatment rather than absent source geometry; ROM-authored colors were found in 40-byte face records

General lesson: cross-platform versions are hypothesis generators. They do not override local N64 evidence, but they can expose what kind of asset/material/runtime relationship to test next.

## 15. Runtime/process ownership lesson

Host02 process ownership is part of the evidence boundary. Heavy probes and emulator sessions can complete while leaving stale ownership rows. Reconcile only after verifying the PID is actually gone.

Do not disable or bypass `STALE_PROCESS_OWNERSHIP_NEEDS_RECONCILIATION` to make work proceed.

Observed recovery pattern:
1. inspect ownership journal
2. check PID existence
3. finish only dead records with evidence
4. rerun preflight

This matters because emulator acceptance can otherwise become entangled with stale instances or ambiguous process identity.

## 16. What is proven versus pending

Proven:
- exact DKR Rev A identity and CIC family
- top-level DKR LUT and major nested bank structure
- DKR RZIP wrapper and >1,000 valid nested decodes
- object-map placement schema and object-definition/model cross-resolution
- level-header object-map slot fields
- native level-selector path and Ancient Lake direct-level experiment
- playable All-Tracks-Unlocked binary patch, user-validated end to end
- source-level Developer Lab compiles and emits a native ROM
- WSL1 is sufficient for the DKR decomp/source-build workflow on Host02
- generic MIPS analyzer improvements are regression-tested in repo

Pending or not promoted:
- explicit Developer Lab menu interaction acceptance
- audio/reverb debug visualization behavior acceptance
- finalized Developer Lab repo package/commit
- proven root cause for the 2026-10-03 black-video incident
- hardened N64 launcher that enforces emulator CWD + single-instance/process evidence
- generalized named-level launcher
- semantic naming of all DKR transition arguments
- full behavior-selector names and placement parameter schemas
- generalization of DKR asset families to unrelated games

## 17. Next clean gates

1. Stabilize emulator acceptance before blaming ROMs.
   - one Mupen instance
   - explicit runtime CWD
   - record PID, ownership ID, plugin/config, ROM hash
   - capture visible frames, not only CPU/audio execution
   - untouched Rev A control first, candidate second

2. Developer Lab visual acceptance.
   Confirm Game Select exposes Developer Lab as a normal visible option. Confirm menu entries, Return behavior, Horseshoe Gulch launch through native level path, and audio/reverb debug ON/OFF behavior.

3. Promote Developer Lab only after acceptance.
   Package only the source patch/recipe and documentation. Do not commit ROMs or unrelated temporary xref files.

4. Add emulator-launch regression fixture.
   Verify config discovery and nonzero video mode under the hardened workspace router. Prefer an explicit launcher CWD over relying on inherited shell state.

5. Continue semantic reverse engineering using local discriminators first.
   Highest-value DKR expansions are behavior-selector naming, placement-parameter schemas, and generalized level-transition arguments.

## 18. Resume checklist for future sessions

Before doing new work:
- read this handoff
- read `knowledge/common/N64_RE_NOTES.md`
- read `docs/workflows/EVIDENCE_WORKFLOW.md`
- read `knowledge/dkr/README.md` for DKR
- inspect the latest relevant workspace checkpoint/report rather than assuming chat state
- run Host02 unified preflight and reconcile dead ownership records if needed
- verify the exact ROM hash before any mutation
- keep web search dormant unless the three-strike rule or an explicit user request activates it

Do not redo already-settled questions unless new evidence contradicts them:
- DKR does not use the initially assumed Rugrats-style top-level table shape
- DKR compression is not generic gzip/zlib; the locally verified wrapper is size + 0x09 + raw DEFLATE + aligned zero padding
- delay slots matter for MIPS call argument recovery
- All-Tracks patch behavior is end-to-end user validated
- a black emulator window with active audio is not sufficient evidence of a bad ROM

This handoff is continuity evidence. Where it conflicts with newer raw receipts/checkpoints, prefer the newer direct evidence and update this document rather than silently carrying stale conclusions forward.
