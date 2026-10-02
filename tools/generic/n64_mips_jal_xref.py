from __future__ import annotations

from pathlib import Path
import argparse
import copy
import json
import struct
from typing import Any

from mips_common import (
    BoundedPropagator,
    REGS,
    branch_target,
    decode,
    is_branch,
    is_delay_slot_source,
    jump_target,
)


def vram_for_offset(offset: int, rom_base: int, vram_base: int) -> int:
    return vram_base + (offset - rom_base)


def read_word(data: bytes, offset: int) -> int | None:
    if offset < 0 or offset + 4 > len(data):
        return None
    return struct.unpack_from(">I", data, offset)[0]
def analysis_window(
    data: bytes,
    call_offset: int,
    lookback: int,
    rom_base: int,
) -> tuple[int, str]:
    raw_start = max(rom_base, call_offset - lookback * 4)
    candidate: int | None = None
    for offset in range(raw_start, call_offset, 4):
        word = read_word(data, offset)
        if word is None:
            break
        op = (word >> 26) & 0x3F
        rs = (word >> 21) & 0x1F
        rt = (word >> 16) & 0x1F
        imm = word & 0xFFFF
        simm = imm if imm < 0x8000 else imm - 0x10000
        if op not in (0x09, 0x19) or rs != 29 or rt != 29 or simm >= 0:
            continue

        saves_ra = False
        for probe in range(offset + 4, min(call_offset, offset + 28), 4):
            probe_word = read_word(data, probe)
            if probe_word is None:
                break
            pop = (probe_word >> 26) & 0x3F
            prs = (probe_word >> 21) & 0x1F
            prt = (probe_word >> 16) & 0x1F
            if pop in (0x2B, 0x3F) and prs == 29 and prt == 31:
                saves_ra = True
                break
        if saves_ra:
            candidate = offset

    if candidate is not None:
        return candidate, "function-entry"
    return raw_start, "window-entry"


def build_context(
    data: bytes,
    call_offset: int,
    lookback: int,
    rom_base: int,
    vram_base: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    delay_source: int | None = None
    start, _entry_prefix = analysis_window(data, call_offset, lookback, rom_base)
    for offset in range(start, call_offset, 4):
        word = read_word(data, offset)
        if word is None:
            break
        pc = vram_for_offset(offset, rom_base, vram_base)
        rows.append(
            {
                "rom_offset": offset,
                "vram": pc,
                "word": f"0x{word:08X}",
                "asm": decode(word, pc),
                "delay_slot_of": (
                    f"0x{delay_source:08X}" if delay_source is not None else None
                ),
            }
        )
        delay_source = pc if is_delay_slot_source(word) else None
    return rows
def propagate_call_state(
    data: bytes,
    call_offset: int,
    lookback: int,
    rom_base: int,
    vram_base: int,
) -> tuple[BoundedPropagator, BoundedPropagator, dict[str, Any] | None]:
    start, entry_prefix = analysis_window(data, call_offset, lookback, rom_base)
    prop = BoundedPropagator(entry_prefix=entry_prefix)
    for offset in range(start, call_offset, 4):
        word = read_word(data, offset)
        if word is None:
            break
        prop.apply(word, vram_for_offset(offset, rom_base, vram_base))

    pre_call = copy.deepcopy(prop)
    call_word = read_word(data, call_offset)
    if call_word is None:
        return pre_call, prop, None

    delay_offset = call_offset + 4
    delay_word = read_word(data, delay_offset)
    delay_row = None
    if delay_word is not None:
        delay_pc = vram_for_offset(delay_offset, rom_base, vram_base)
        delay_row = {
            "rom_offset": delay_offset,
            "vram": delay_pc,
            "word": f"0x{delay_word:08X}",
            "asm": decode(delay_word, delay_pc),
            "delay_slot_of": f"0x{vram_for_offset(call_offset, rom_base, vram_base):08X}",
        }
        prop.apply(delay_word, delay_pc)

    return pre_call, prop, delay_row
def recovered_arguments(prop: BoundedPropagator) -> dict[str, Any]:
    args: dict[str, Any] = {}
    for reg in range(4, 8):
        value = prop.get(reg)
        args[REGS[reg]] = value.to_dict() if value is not None else None

    stack_args: dict[str, Any] = {}
    for abstract_offset, value in sorted(prop.stack.items()):
        current_offset = abstract_offset - prop.sp_bias
        if (
            0x10 <= current_offset <= 0x40
            and current_offset % 4 == 0
            and (value.sources or value.kind != "entry-stack")
        ):
            stack_args[f"sp+0x{current_offset:X}"] = value.to_dict()
    return {"registers": args, "stack": stack_args}


def recover_jalr_target(word: int, prop: BoundedPropagator) -> dict[str, Any] | None:
    op = (word >> 26) & 0x3F
    fn = word & 0x3F
    if op != 0 or fn != 0x09:
        return None
    rs = (word >> 21) & 0x1F
    value = prop.get(rs)
    if value is None or value.value is None:
        return None
    return {
        "source_register": REGS[rs],
        "target": value.value & 0xFFFFFFFF,
        "target_hex": f"0x{value.value & 0xFFFFFFFF:08X}",
        "provenance": value.to_dict(),
    }
def local_control_flow(
    context: list[dict[str, Any]],
    call_pc: int,
    call_word: int,
    call_target: int,
    delay_row: dict[str, Any] | None,
    indirect: bool,
) -> dict[str, Any]:
    nodes = list(context)
    nodes.append(
        {
            "rom_offset": None,
            "vram": call_pc,
            "word": f"0x{call_word:08X}",
            "asm": decode(call_word, call_pc),
            "delay_slot_of": None,
        }
    )
    if delay_row is not None:
        nodes.append(delay_row)

    edges: list[dict[str, Any]] = []
    for row in context:
        word = int(str(row["word"]), 16)
        pc = int(row["vram"])
        op = (word >> 26) & 0x3F
        if is_branch(word):
            edges.append(
                {
                    "source": f"0x{pc:08X}",
                    "kind": "branch",
                    "target": f"0x{branch_target(word, pc):08X}",
                    "fallthrough": f"0x{(pc + 8) & 0xFFFFFFFF:08X}",
                    "delay_slot": f"0x{(pc + 4) & 0xFFFFFFFF:08X}",
                }
            )
        elif op in (0x02, 0x03):
            edges.append(
                {
                    "source": f"0x{pc:08X}",
                    "kind": "call" if op == 0x03 else "jump",
                    "target": f"0x{jump_target(word, pc):08X}",
                    "delay_slot": f"0x{(pc + 4) & 0xFFFFFFFF:08X}",
                }
            )
    edges.append(
        {
            "source": f"0x{call_pc:08X}",
            "kind": "call_indirect" if indirect else "call_direct",
            "target": f"0x{call_target:08X}",
            "delay_slot": f"0x{(call_pc + 4) & 0xFFFFFFFF:08X}",
            "return": f"0x{(call_pc + 8) & 0xFFFFFFFF:08X}",
        }
    )
    return {"nodes": nodes, "control_edges": edges}


def analyze_xrefs(
    data: bytes,
    target: int,
    *,
    rom_base: int = 0x1000,
    vram_base: int = 0x80000400,
    lookback: int = 12,
) -> dict[str, Any]:
    target &= 0xFFFFFFFF
    hits: list[dict[str, Any]] = []

    for offset in range(rom_base, len(data) - 3, 4):
        word = read_word(data, offset)
        if word is None:
            break
        op = (word >> 26) & 0x3F
        fn = word & 0x3F
        is_direct = op == 0x03
        is_indirect = op == 0x00 and fn == 0x09
        if not is_direct and not is_indirect:
            continue

        pc = vram_for_offset(offset, rom_base, vram_base)
        pre, at_callee, delay_row = propagate_call_state(
            data, offset, lookback, rom_base, vram_base
        )
        recovered_indirect = recover_jalr_target(word, pre) if is_indirect else None
        if is_direct:
            call_target = jump_target(word, pc)
        elif recovered_indirect is not None:
            call_target = int(recovered_indirect["target"])
        else:
            continue

        if (call_target & 0xFFFFFFFF) != target:
            continue

        context = build_context(data, offset, lookback, rom_base, vram_base)
        arguments = recovered_arguments(at_callee)
        a0 = arguments["registers"]["a0"]
        hit = {
            "call_rom_offset": offset,
            "call_vram": pc,
            "return_vram": (pc + 8) & 0xFFFFFFFF,
            "call_kind": "jalr" if is_indirect else "jal",
            "call_word": f"0x{word:08X}",
            "target": f"0x{call_target:08X}",
            "recovered_indirect_target": recovered_indirect,
            "arguments": arguments,
            "nearest_a0_constant": a0["value"] if a0 is not None and a0.get("value") is not None else None,
            "delay_slot": delay_row,
            "context": context,
            "analysis_limits": {
                "lookback_instructions": lookback,
                "bounded_linear_propagation": True,
                "control_flow_seen_in_context": pre.control_flow_seen,
                "entry_anchor": analysis_window(data, offset, lookback, rom_base)[1],
                "analysis_start_vram": f"0x{vram_for_offset(analysis_window(data, offset, lookback, rom_base)[0], rom_base, vram_base):08X}",
            },
        }
        hit["local_cfg"] = local_control_flow(
            context, pc, word, call_target, delay_row, is_indirect
        )
        hits.append(hit)

    return {
        "schema": "n64.mips_call_xref.v2",
        "target": f"0x{target:08X}",
        "hit_count": len(hits),
        "hits": hits,
    }
def main() -> int:
    ap = argparse.ArgumentParser(
        description="Delay-slot-aware N64 JAL/JALR xref analyzer with bounded value propagation."
    )
    ap.add_argument("rom")
    ap.add_argument("--target", required=True, type=lambda x: int(x, 0))
    ap.add_argument("--rom-base", type=lambda x: int(x, 0), default=0x1000)
    ap.add_argument("--vram-base", type=lambda x: int(x, 0), default=0x80000400)
    ap.add_argument("--lookback", type=int, default=12)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    report = analyze_xrefs(
        Path(args.rom).read_bytes(),
        args.target,
        rom_base=args.rom_base,
        vram_base=args.vram_base,
        lookback=args.lookback,
    )
    Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")

    summary = {
        "target": report["target"],
        "hit_count": report["hit_count"],
        "calls": [
            {
                "call_vram": f"0x{int(hit['call_vram']):08X}",
                "return_vram": f"0x{int(hit['return_vram']):08X}",
                "kind": hit["call_kind"],
                "arguments": hit["arguments"],
            }
            for hit in report["hits"]
        ],
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
