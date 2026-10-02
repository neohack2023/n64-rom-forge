from __future__ import annotations

from dataclasses import dataclass
from typing import Any

REGS = [
    "zero", "at", "v0", "v1", "a0", "a1", "a2", "a3",
    "t0", "t1", "t2", "t3", "t4", "t5", "t6", "t7",
    "s0", "s1", "s2", "s3", "s4", "s5", "s6", "s7",
    "t8", "t9", "k0", "k1", "gp", "sp", "fp", "ra",
]

MASK32 = 0xFFFFFFFF
MASK64 = 0xFFFFFFFFFFFFFFFF

REGIMM_BRANCHES = {
    0x00: "bltz",
    0x01: "bgez",
    0x02: "bltzl",
    0x03: "bgezl",
    0x10: "bltzal",
    0x11: "bgezal",
    0x12: "bltzall",
    0x13: "bgezall",
}
def sx16(value: int) -> int:
    return value if value < 0x8000 else value - 0x10000


def jump_target(word: int, pc: int) -> int:
    return ((pc + 4) & 0xF0000000) | ((word & 0x03FFFFFF) << 2)


def branch_target(word: int, pc: int) -> int:
    return (pc + 4 + (sx16(word & 0xFFFF) << 2)) & MASK32


def is_delay_slot_source(word: int) -> bool:
    op = (word >> 26) & 0x3F
    if op in (0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x14, 0x15, 0x16, 0x17):
        return True
    if op == 0x01:
        return ((word >> 16) & 0x1F) in REGIMM_BRANCHES
    if op == 0x00:
        return (word & 0x3F) in (0x08, 0x09)
    return False


def is_branch(word: int) -> bool:
    op = (word >> 26) & 0x3F
    return op in (0x04, 0x05, 0x06, 0x07, 0x14, 0x15, 0x16, 0x17) or (
        op == 0x01 and ((word >> 16) & 0x1F) in REGIMM_BRANCHES
    )
def decode(word: int, pc: int) -> str:
    op = (word >> 26) & 0x3F
    rs = (word >> 21) & 0x1F
    rt = (word >> 16) & 0x1F
    rd = (word >> 11) & 0x1F
    sa = (word >> 6) & 0x1F
    fn = word & 0x3F
    imm = word & 0xFFFF

    if word == 0:
        return "nop"

    if op == 0x00:
        shifts = {
            0x00: "sll", 0x02: "srl", 0x03: "sra",
            0x38: "dsll", 0x3A: "dsrl", 0x3B: "dsra",
            0x3C: "dsll32", 0x3E: "dsrl32", 0x3F: "dsra32",
        }
        var_shifts = {
            0x04: "sllv", 0x06: "srlv", 0x07: "srav",
            0x14: "dsllv", 0x16: "dsrlv", 0x17: "dsrav",
        }
        alu = {
            0x20: "add", 0x21: "addu", 0x22: "sub", 0x23: "subu",
            0x24: "and", 0x25: "or", 0x26: "xor", 0x27: "nor",
            0x2A: "slt", 0x2B: "sltu",
            0x2C: "dadd", 0x2D: "daddu", 0x2E: "dsub", 0x2F: "dsubu",
        }
        if fn in shifts:
            return f"{shifts[fn]} {REGS[rd]},{REGS[rt]},{sa}"
        if fn in var_shifts:
            return f"{var_shifts[fn]} {REGS[rd]},{REGS[rt]},{REGS[rs]}"
        if fn == 0x08:
            return f"jr {REGS[rs]}"
        if fn == 0x09:
            return f"jalr {REGS[rd]},{REGS[rs]}"
        if fn in alu:
            return f"{alu[fn]} {REGS[rd]},{REGS[rs]},{REGS[rt]}"
        if fn in (0x18, 0x19, 0x1C, 0x1D):
            name = {0x18: "mult", 0x19: "multu", 0x1C: "dmult", 0x1D: "dmultu"}[fn]
            return f"{name} {REGS[rs]},{REGS[rt]}"
        if fn in (0x1A, 0x1B, 0x1E, 0x1F):
            name = {0x1A: "div", 0x1B: "divu", 0x1E: "ddiv", 0x1F: "ddivu"}[fn]
            return f"{name} {REGS[rs]},{REGS[rt]}"
        if fn in (0x10, 0x12):
            return f"{'mfhi' if fn == 0x10 else 'mflo'} {REGS[rd]}"
        if fn in (0x11, 0x13):
            return f"{'mthi' if fn == 0x11 else 'mtlo'} {REGS[rs]}"
        return f".word 0x{word:08X}"

    if op in (0x02, 0x03):
        return f"{'j' if op == 0x02 else 'jal'} 0x{jump_target(word, pc):08X}"
    branch_names = {
        0x04: "beq", 0x05: "bne", 0x06: "blez", 0x07: "bgtz",
        0x14: "beql", 0x15: "bnel", 0x16: "blezl", 0x17: "bgtzl",
    }
    if op in branch_names:
        name = branch_names[op]
        target = branch_target(word, pc)
        if op in (0x04, 0x05, 0x14, 0x15):
            return f"{name} {REGS[rs]},{REGS[rt]},0x{target:08X}"
        return f"{name} {REGS[rs]},0x{target:08X}"

    if op == 0x01:
        name = REGIMM_BRANCHES.get(rt)
        if name:
            return f"{name} {REGS[rs]},0x{branch_target(word, pc):08X}"
        return f"regimm rt={rt} {REGS[rs]},0x{branch_target(word, pc):08X}"

    immediates = {
        0x08: "addi", 0x09: "addiu", 0x0A: "slti", 0x0B: "sltiu",
        0x0C: "andi", 0x0D: "ori", 0x0E: "xori",
        0x18: "daddi", 0x19: "daddiu",
    }
    if op in immediates:
        value = imm if op in (0x0C, 0x0D, 0x0E) else sx16(imm)
        shown = f"0x{value:04X}" if op in (0x0C, 0x0D, 0x0E) else str(value)
        return f"{immediates[op]} {REGS[rt]},{REGS[rs]},{shown}"

    if op == 0x0F:
        return f"lui {REGS[rt]},0x{imm:04X}"
    memory = {
        0x1A: "ldl", 0x1B: "ldr",
        0x20: "lb", 0x21: "lh", 0x22: "lwl", 0x23: "lw",
        0x24: "lbu", 0x25: "lhu", 0x26: "lwr", 0x27: "lwu",
        0x28: "sb", 0x29: "sh", 0x2A: "swl", 0x2B: "sw",
        0x2C: "sdl", 0x2D: "sdr", 0x2E: "swr",
        0x30: "ll", 0x34: "lld", 0x37: "ld",
        0x38: "sc", 0x3C: "scd", 0x3F: "sd",
    }
    if op in memory:
        return f"{memory[op]} {REGS[rt]},{sx16(imm)}({REGS[rs]})"

    if op in (0x16, 0x17):
        # Branch-likely opcodes are handled above. This keeps future table edits fail-safe.
        return f".word 0x{word:08X}"

    if op in (0x10, 0x11, 0x12, 0x13):
        return f"cop{op - 0x10} 0x{word & 0x03FFFFFF:07X}"

    return f".word 0x{word:08X}"


@dataclass
class Value:
    value: int | None
    sources: tuple[int, ...]
    kind: str = "constant"
    symbol: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "value_hex": f"0x{self.value & MASK64:X}" if self.value is not None else None,
            "symbol": self.symbol,
            "sources": [f"0x{x:08X}" for x in self.sources],
            "kind": self.kind,
        }


class BoundedPropagator:
    CALLER_SAVED = set(range(1, 16)) | {24, 25, 31}

    def __init__(self, entry_prefix: str = "window-entry") -> None:
        self.entry_prefix = entry_prefix
        self.regs: dict[int, Value] = {0: Value(0, (), "zero", "zero")}
        for reg in range(4, 8):
            self.regs[reg] = Value(
                None, (), "entry-register", f"{entry_prefix}:{REGS[reg]}"
            )
        self.stack: dict[int, Value] = {
            off: Value(None, (), "entry-stack", f"{entry_prefix}:sp+0x{off:X}")
            for off in range(0x10, 0x44, 4)
        }
        self.sp_bias = 0
        self.control_flow_seen = False
        self.pending_call_clobber = False
    def get(self, reg: int) -> Value | None:
        return self.regs.get(reg)

    def set(self, reg: int, value: Value | None) -> None:
        if reg == 0:
            return
        if value is None:
            self.regs.pop(reg, None)
        else:
            self.regs[reg] = value

    def _combine(self, pc: int, *values: Value) -> tuple[int, ...]:
        sources: list[int] = []
        for value in values:
            sources.extend(value.sources)
        sources.append(pc)
        return tuple(dict.fromkeys(sources))

    def _copy(self, value: Value, pc: int, kind: str) -> Value:
        return Value(value.value, self._combine(pc, value), kind, value.symbol)

    def _clobber_caller_saved(self) -> None:
        for reg in self.CALLER_SAVED:
            self.regs.pop(reg, None)

    def _finish(self, clobber_after: bool, *, new_call: bool = False) -> None:
        if clobber_after:
            self._clobber_caller_saved()
        if new_call:
            self.pending_call_clobber = True

    def apply(self, word: int, pc: int) -> None:
        clobber_after = self.pending_call_clobber
        self.pending_call_clobber = False
        op = (word >> 26) & 0x3F
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        rd = (word >> 11) & 0x1F
        sa = (word >> 6) & 0x1F
        fn = word & 0x3F
        imm = word & 0xFFFF
        simm = sx16(imm)

        if is_delay_slot_source(word):
            self.control_flow_seen = True
        if op == 0x0F:
            self.set(rt, Value((imm << 16) & MASK32, (pc,), "lui"))
            self._finish(clobber_after)
            return

        if op in (0x08, 0x09, 0x18, 0x19):
            base = self.get(rs)
            if rt == 29 and rs == 29:
                self.sp_bias += simm
                self.set(rt, None)
                self._finish(clobber_after)
                return
            if base is not None:
                if base.value is not None:
                    mask = MASK64 if op in (0x18, 0x19) else MASK32
                    self.set(
                        rt,
                        Value(
                            (base.value + simm) & mask,
                            self._combine(pc, base),
                            "add-immediate",
                            base.symbol,
                        ),
                    )
                elif base.symbol is not None:
                    expr = base.symbol if simm == 0 else f"({base.symbol}{simm:+d})"
                    self.set(rt, Value(None, self._combine(pc, base), "symbolic-add", expr))
                else:
                    self.set(rt, None)
            else:
                self.set(rt, None)
            self._finish(clobber_after)
            return

        if op in (0x0C, 0x0D, 0x0E):
            base = self.get(rs)
            if base is None:
                self.set(rt, None)
            elif base.value is not None:
                value = {
                    0x0C: base.value & imm,
                    0x0D: base.value | imm,
                    0x0E: base.value ^ imm,
                }[op]
                self.set(rt, Value(value & MASK64, self._combine(pc, base), "logical-immediate"))
            elif imm == 0:
                self.set(rt, self._copy(base, pc, "move"))
            else:
                opname = {0x0C: "&", 0x0D: "|", 0x0E: "^"}[op]
                self.set(
                    rt,
                    Value(None, self._combine(pc, base), "symbolic-logical", f"({base.symbol}{opname}0x{imm:X})"),
                )
            self._finish(clobber_after)
            return
        if op == 0x00:
            left = self.get(rs)
            right = self.get(rt)
            if fn in (0x21, 0x25, 0x2D):
                zero_left = left is not None and left.value == 0 and left.symbol in (None, "zero")
                zero_right = right is not None and right.value == 0 and right.symbol in (None, "zero")
                if zero_left and right is not None:
                    self.set(rd, self._copy(right, pc, "move"))
                elif zero_right and left is not None:
                    self.set(rd, self._copy(left, pc, "move"))
                elif left is not None and right is not None and left.value is not None and right.value is not None:
                    value = (left.value | right.value) if fn == 0x25 else (left.value + right.value)
                    self.set(rd, Value(value & MASK64, self._combine(pc, left, right), "move-or-add"))
                else:
                    self.set(rd, None)
                self._finish(clobber_after)
                return

            if fn in (0x00, 0x38, 0x3C):
                if right is not None and sa == 0:
                    self.set(rd, self._copy(right, pc, "move"))
                elif right is not None and right.value is not None:
                    shift = sa + (32 if fn == 0x3C else 0)
                    mask = MASK64 if fn in (0x38, 0x3C) else MASK32
                    self.set(rd, Value((right.value << shift) & mask, self._combine(pc, right), "shift"))
                else:
                    self.set(rd, None)
                self._finish(clobber_after)
                return

            if fn == 0x09:
                self.set(rd, Value((pc + 8) & MASK32, (pc,), "return-address"))
                self._finish(clobber_after, new_call=True)
                return

            if fn != 0x08:
                self.set(rd, None)
            self._finish(clobber_after)
            return
        if op in (0x23, 0x27, 0x37) and rs == 29:
            key = self.sp_bias + simm
            value = self.stack.get(key)
            self.set(rt, self._copy(value, pc, "stack-reload") if value else None)
            self._finish(clobber_after)
            return

        if op in (0x2B, 0x3F) and rs == 29:
            key = self.sp_bias + simm
            value = self.get(rt)
            if value is None:
                self.stack.pop(key, None)
            else:
                self.stack[key] = self._copy(value, pc, "stack-store")
            self._finish(clobber_after)
            return

        if op == 0x03:
            self.set(31, Value((pc + 8) & MASK32, (pc,), "return-address"))
            self._finish(clobber_after, new_call=True)
            return

        if op in (0x1A, 0x1B, 0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x30, 0x34, 0x37):
            self.set(rt, None)
        elif op in (0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x18, 0x19):
            self.set(rt, None)
        self._finish(clobber_after)
