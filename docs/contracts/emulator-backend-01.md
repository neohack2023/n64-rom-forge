# N64RF_EMULATOR_BACKEND_01

Status: FROZEN CONTRACT CANDIDATE
Scope: n64-rom-forge
Execution state: NO_ROM / NO_EMULATOR_REQUIRED

## Purpose

Define the emulator backend surface consumed by N64 ROM Forge without coupling the workbench to one emulator implementation.

The contract is observation-first. It allows execution control required for debugging, but it does not expose mutation of emulated memory, CPU registers, ROM bytes, instructions, assets, or arbitrary state injection.

## Required operations

Every conforming backend MUST provide these semantic operations.

### Execution control

- `pause() -> BackendState`
- `run() -> BackendState`
- `step(count=1) -> StepResult`

`step` is instruction stepping unless a backend explicitly reports a different granularity. A backend that cannot provide instruction stepping MUST fail closed rather than silently substitute frame stepping.

### Memory observation

- `read_memory(address, length, *, address_space="virtual") -> MemoryRead`

Requirements:
- read-only
- address and length are receipt-visible
- backend must report the effective address space
- backend-specific reads with side effects must be documented by the adapter
- unsupported regions fail closed

### Register observation

- `read_registers(register_set="r4300") -> RegisterSnapshot`

Minimum normalized R4300 set:
- GPR 0..31
- PC
- HI
- LO

Backend-specific COP0/FPU/RSP registers MAY be exposed as capability-gated extensions.

### Instruction decode

- `decode_instruction(address) -> DecodedInstruction`

Normalized result:
- address
- raw 32-bit instruction when available
- mnemonic
- operands
- backend-native text, optional

### Address translation

- `virtual_to_physical(address) -> AddressTranslation`

Requirements:
- explicit success/failure
- input and output address spaces recorded
- no guessed translation

### Breakpoint management

- `list_breakpoints() -> list[Breakpoint]`
- `add_observation_breakpoint(spec) -> Breakpoint`
- `remove_observation_breakpoint(id) -> None`
- `read_last_breakpoint_trigger() -> BreakpointTrigger | None`

Breakpoint kinds MAY include execute, memory-read, and memory-write observation triggers when supported by the backend. A memory-write breakpoint observes the emulated program performing a write; it does NOT grant N64RF permission to write memory.

### Frame / VI markers

- `subscribe_frame_markers(callback) -> Subscription`
- `unsubscribe_frame_markers(subscription_id) -> None`

Normalized marker:
- monotonically increasing backend-local marker sequence
- backend event type, e.g. `VI`
- observed PC when available
- backend timestamp/tick when available

A VI callback is treated as an emulator timing marker, not automatically as a rendered-frame proof.

## Required state/capability discovery

Every backend MUST expose:

- `backend_identity() -> BackendIdentity`
- `capabilities() -> BackendCapabilities`
- `read_debugger_state() -> BackendState`

`BackendIdentity` MUST include:
- backend_id
- repository/source identity when applicable
- pinned revision/commit when known
- build digest when known
- adapter implementation version

`BackendCapabilities` MUST distinguish:
- required capabilities supported
- optional capabilities supported
- denied capabilities
- unsupported capabilities

## Explicitly denied operations

The public N64RF emulator backend contract MUST NOT define or expose:

- `write_memory`
- `write_register`
- `set_pc`
- `inject_code`
- `patch_instruction`
- `modify_rom`
- `alter_asset`
- arbitrary save-state injection
- arbitrary controller mutation
- arbitrary backend command passthrough

An implementation wrapping an upstream emulator that has write APIs MUST structurally omit them from the N64RF-facing interface.

## Fail-closed behavior

Unknown/unsupported operations MUST return a typed unsupported-capability result or raise the contract-defined capability error.

Backends MUST NOT:
- silently coerce unsupported step granularity
- infer an address translation
- substitute an unverified memory region
- expose raw backend command channels that bypass this contract

Rejected operations are evidence and SHOULD be persisted in later probe receipts.

## Semantic parity rule

Backend parity is semantic, not API-identical.

Example:
- Mupen64Plus may implement frame markers through debugger VI callbacks.
- ares may implement observations through a GDB-oriented surface.

Both can conform if they emit the same normalized N64RF observation types.

## Game Adapter coupling

The preferred AI-facing path is:

semantic concept/symbol
-> revision-locked Game Adapter resolution
-> bounded observation address/range
-> emulator backend operation
-> observation receipt

Raw-address requests are an expert reverse-engineering lane and must record:
- address
- address space
- game adapter/revision
- evidence source
- confidence

## Out of scope for this contract

- persistent SQLite schema
- deterministic controller-route execution
- save-state policy
- ares oracle comparison policy
- hardware witness protocol
- runtime knowledge promotion

Those belong to sibling contracts.

## Research-resolved backend notes

### Mupen64Plus

Current upstream debugger API supports:
- debugger init/update/VI callbacks
- RUNNING / STEPPING / PAUSED states
- single instruction stepping
- R4300 instruction decode helper
- 8/16/32/64-bit memory reads
- CPU register pointers
- breakpoint lookup/commands/trigger reason
- virtual-to-physical translation

Upstream also exposes `DebugMemWrite*`. These functions are intentionally excluded from N64RF.

For the console debugger, upstream documentation advises using interpreter mode because dynarec can cause debugger API issues.

### ares

Current N64 source exposes:
- MIPS:4000 GDB target
- virtual-address normalization/devirtualization
- CPU-like memory reads
- general/COP0/FPU register reads
- deterministic entropy setting

ares also exposes debugger memory/register write hooks. A future N64RF ares adapter must allow-list read/control packets and reject writes.

## Conformance minimum

Before any ROM-backed run is authorized, a backend implementation must pass no-ROM/mock conformance tests proving:

1. all required semantic methods exist;
2. denied write/mutation methods are absent from the public interface;
3. unsupported operations fail closed;
4. frame-marker subscription can be normalized;
5. breakpoint trigger metadata can be normalized;
6. address-space metadata is preserved;
7. backend identity/capability state is receipt-ready.
