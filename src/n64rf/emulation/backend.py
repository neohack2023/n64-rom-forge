from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Mapping, Sequence


class CapabilityError(RuntimeError):
    """Raised when a backend cannot safely provide a requested capability."""


class RunState(str, Enum):
    RUNNING = "running"
    PAUSED = "paused"
    STEPPING = "stepping"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class BackendIdentity:
    backend_id: str
    repository: str | None = None
    revision: str | None = None
    build_digest: str | None = None
    adapter_version: str = "n64rf.emulator-backend.v1"


@dataclass(frozen=True)
class BackendCapabilities:
    required: frozenset[str]
    optional: frozenset[str] = frozenset()
    denied: frozenset[str] = frozenset({
        "write_memory",
        "write_register",
        "set_pc",
        "inject_code",
        "patch_instruction",
        "modify_rom",
        "alter_asset",
        "arbitrary_save_state_injection",
        "arbitrary_controller_mutation",
        "raw_backend_command",
    })
    unsupported: frozenset[str] = frozenset()


@dataclass(frozen=True)
class BackendState:
    run_state: RunState
    pc: int | None = None
    detail: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class StepResult:
    requested_count: int
    completed_count: int
    state: BackendState


@dataclass(frozen=True)
class MemoryRead:
    address: int
    length: int
    data: bytes
    address_space: str = "virtual"
    effective_address_space: str = "virtual"


@dataclass(frozen=True)
class RegisterSnapshot:
    register_set: str
    values: Mapping[str, int]


@dataclass(frozen=True)
class DecodedInstruction:
    address: int
    raw: int | None
    mnemonic: str
    operands: str = ""
    backend_text: str | None = None


@dataclass(frozen=True)
class AddressTranslation:
    input_address: int
    output_address: int | None
    input_space: str = "virtual"
    output_space: str = "physical"
    resolved: bool = True


@dataclass(frozen=True)
class BreakpointSpec:
    kind: str
    address: int
    size: int = 1
    address_space: str = "virtual"


@dataclass(frozen=True)
class Breakpoint:
    id: str
    spec: BreakpointSpec
    enabled: bool = True


@dataclass(frozen=True)
class BreakpointTrigger:
    breakpoint_id: str | None
    kind: str
    pc: int | None = None
    accessed_address: int | None = None
    accessed_address_space: str | None = None


@dataclass(frozen=True)
class FrameMarker:
    sequence: int
    event_type: str
    pc: int | None = None
    tick: int | None = None


FrameMarkerCallback = Callable[[FrameMarker], None]


class EmulatorBackend(ABC):
    CONTRACT_ID = "N64RF_EMULATOR_BACKEND_01"
    REQUIRED_CAPABILITIES = frozenset({
        "pause",
        "run",
        "step",
        "read_memory",
        "read_registers",
        "decode_instruction",
        "virtual_to_physical",
        "list_breakpoints",
        "add_observation_breakpoint",
        "remove_observation_breakpoint",
        "read_last_breakpoint_trigger",
        "subscribe_frame_markers",
        "unsubscribe_frame_markers",
        "read_debugger_state",
        "backend_identity",
        "capabilities",
    })

    @abstractmethod
    def backend_identity(self) -> BackendIdentity: ...

    @abstractmethod
    def capabilities(self) -> BackendCapabilities: ...

    @abstractmethod
    def read_debugger_state(self) -> BackendState: ...

    @abstractmethod
    def pause(self) -> BackendState: ...

    @abstractmethod
    def run(self) -> BackendState: ...

    @abstractmethod
    def step(self, count: int = 1) -> StepResult: ...

    @abstractmethod
    def read_memory(
        self, address: int, length: int, *, address_space: str = "virtual"
    ) -> MemoryRead: ...

    @abstractmethod
    def read_registers(self, register_set: str = "r4300") -> RegisterSnapshot: ...

    @abstractmethod
    def decode_instruction(self, address: int) -> DecodedInstruction: ...

    @abstractmethod
    def virtual_to_physical(self, address: int) -> AddressTranslation: ...

    @abstractmethod
    def list_breakpoints(self) -> Sequence[Breakpoint]: ...

    @abstractmethod
    def add_observation_breakpoint(self, spec: BreakpointSpec) -> Breakpoint: ...

    @abstractmethod
    def remove_observation_breakpoint(self, breakpoint_id: str) -> None: ...

    @abstractmethod
    def read_last_breakpoint_trigger(self) -> BreakpointTrigger | None: ...

    @abstractmethod
    def subscribe_frame_markers(self, callback: FrameMarkerCallback) -> str: ...

    @abstractmethod
    def unsubscribe_frame_markers(self, subscription_id: str) -> None: ...
