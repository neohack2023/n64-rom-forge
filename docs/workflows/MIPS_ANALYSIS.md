# N64 MIPS analysis tooling

The generic MIPS lane is intentionally small and evidence-oriented. It is not a replacement for a full decompiler.

## Decoder

`tools/generic/mips32_be_disasm_min.py` decodes big-endian VR4300/MIPS III code using explicit ROM-to-VRAM mapping.

Supported families now include:

- J/JAL and JR/JALR
- BEQ/BNE/BLEZ/BGTZ and branch-likely forms
- REGIMM branches including link/likely variants
- 32-bit integer arithmetic/logical instructions
- DADD/DADDU/DSUB/DSUBU and DADDI/DADDIU
- DSLL/DSRL/DSRA, *32 variants, and variable 64-bit shifts
- LWU, LDL/LDR, LD, SDL/SDR, SD, LLD/SCD
- common byte/halfword/word loads and stores

Plain-text disassembly marks the next instruction with `delay_slot_of=0x...`. `--json` emits the same fact as structured metadata.
## Call XREF analyzer

`tools/generic/n64_mips_jal_xref.py` resolves direct JAL calls and statically recoverable JALR calls to a requested target.

Its bounded propagator understands:

- LUI + ADDIU/DADDIU
- LUI + ORI and simple logical immediates
- zero-register moves via OR/ADDU/DADDU
- stack-frame adjustment
- SW/SD save followed by LW/LWU/LD reload
- caller-saved clobber after intervening calls
- delay-slot writes before the target callee observes arguments

Recovered values retain provenance PCs.

A recognized `addiu/daddiu sp,sp,-N` plus RA save anchors symbols as `function-entry:...`. Without that evidence, unknown initial values are labeled `window-entry:...`, not function arguments.
## JALR admission

An indirect call is emitted as a target XREF only when the JALR source register has a concrete statically recovered numeric value before the delay slot executes.

A symbolic source such as `function-entry:a0` is not promoted into a guessed address.

## Local CFG slice

Each XREF hit includes `local_cfg`:

- context nodes
- direct branch targets and fallthroughs
- direct jump/call targets
- recovered target for admitted JALR calls
- delay-slot PC
- return PC for calls

This is a bounded control-flow slice around the callsite, not a claim that arbitrary ROM bytes form a complete function graph.

## Limits

The propagator is deliberately not path-sensitive. If branches/calls occur in the lookback window, `analysis_limits.control_flow_seen_in_context` records that fact.

Unknown memory loads remain unknown unless they are modeled stack reloads. For example, a value loaded from a global address is not guessed merely because its base address is statically known.

ROM overlays still require the caller to supply the correct `--rom-base` and `--vram-base`. There is no universal N64 ROM-offset to KSEG0 mapping.
