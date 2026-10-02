from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERIC = ROOT / "tools" / "generic"
sys.path.insert(0, str(GENERIC))

from mips_common import decode
from mips32_be_disasm_min import disassemble
from n64_mips_jal_xref import analyze_xrefs


def r(rs: int, rt: int, rd: int, sa: int, fn: int) -> int:
    return (rs << 21) | (rt << 16) | (rd << 11) | (sa << 6) | fn


def i(op: int, rs: int, rt: int, imm: int) -> int:
    return (op << 26) | (rs << 21) | (rt << 16) | (imm & 0xFFFF)


def j(op: int, target: int) -> int:
    return (op << 26) | ((target >> 2) & 0x03FFFFFF)


def words(*items: int) -> bytes:
    return b"".join(item.to_bytes(4, "big") for item in items)
class DecoderCoverageTests(unittest.TestCase):
    def test_mips3_integer_and_memory_family(self) -> None:
        pc = 0x80001000
        self.assertEqual(decode(r(8, 9, 10, 0, 0x2D), pc), "daddu t2,t0,t1")
        self.assertEqual(decode(r(8, 9, 10, 0, 0x2F), pc), "dsubu t2,t0,t1")
        self.assertEqual(decode(i(0x19, 8, 9, -4), pc), "daddiu t1,t0,-4")
        self.assertEqual(decode(i(0x1A, 29, 8, 16), pc), "ldl t0,16(sp)")
        self.assertEqual(decode(i(0x1B, 29, 8, 16), pc), "ldr t0,16(sp)")
        self.assertEqual(decode(i(0x27, 29, 8, 16), pc), "lwu t0,16(sp)")
        self.assertEqual(decode(i(0x37, 29, 8, 24), pc), "ld t0,24(sp)")
        self.assertEqual(decode(i(0x3F, 29, 8, 24), pc), "sd t0,24(sp)")
        self.assertEqual(decode(r(0, 8, 9, 3, 0x38), pc), "dsll t1,t0,3")
        self.assertEqual(decode(r(0, 8, 9, 3, 0x3E), pc), "dsrl32 t1,t0,3")

    def test_remaining_branch_forms(self) -> None:
        pc = 0x80001000
        self.assertTrue(decode(i(0x14, 4, 5, 2), pc).startswith("beql a0,a1,"))
        self.assertTrue(decode(i(0x17, 4, 0, 2), pc).startswith("bgtzl a0,"))
        self.assertTrue(decode(i(0x01, 4, 0x11, 2), pc).startswith("bgezal a0,"))


class DelaySlotTests(unittest.TestCase):
    def test_disassembler_marks_delay_slot(self) -> None:
        base = 0x80000000
        data = words(
            j(0x03, 0x80000100),
            i(0x09, 0, 5, 20),
            0,
        )
        rows = disassemble(data, base, 3, rom_base=0, vram_base=base)
        self.assertIsNone(rows[0]["delay_slot_of"])
        self.assertEqual(rows[1]["delay_slot_of"], "0x80000000")
        self.assertIsNone(rows[2]["delay_slot_of"])
class XrefPropagationTests(unittest.TestCase):
    def test_direct_call_reconstructs_arguments_and_stack_reload(self) -> None:
        base = 0x80000000
        target = 0x80000100
        data = words(
            i(0x0F, 0, 4, 0x8012),          # lui a0,0x8012
            i(0x09, 4, 4, 0x3456),          # addiu a0,a0,0x3456
            r(4, 0, 5, 0, 0x21),            # addu a1,a0,zero
            i(0x2B, 29, 5, 0x10),           # sw a1,0x10(sp)
            i(0x23, 29, 5, 0x10),           # lw a1,0x10(sp)
            j(0x03, target),                 # jal target
            i(0x09, 0, 6, 7),               # addiu a2,zero,7 (delay)
            0,
        )
        report = analyze_xrefs(data, target, rom_base=0, vram_base=base, lookback=8)
        self.assertEqual(report["hit_count"], 1)
        args = report["hits"][0]["arguments"]
        self.assertEqual(args["registers"]["a0"]["value"], 0x80123456)
        self.assertEqual(args["registers"]["a1"]["value"], 0x80123456)
        self.assertEqual(args["registers"]["a2"]["value"], 7)
        self.assertEqual(args["stack"]["sp+0x10"]["value"], 0x80123456)
        self.assertEqual(report["hits"][0]["delay_slot"]["delay_slot_of"], "0x80000014")
        cfg_edges = report["hits"][0]["local_cfg"]["control_edges"]
        self.assertTrue(
            any(
                edge["kind"] == "call_direct" and edge["target"] == "0x80000100"
                for edge in cfg_edges
            )
        )
    def test_jalr_target_is_recovered_before_delay_slot_mutates_source(self) -> None:
        base = 0x80000000
        target = 0x80000200
        data = words(
            i(0x0F, 0, 25, 0x8000),         # lui t9,0x8000
            i(0x0D, 25, 25, 0x0200),        # ori t9,t9,0x0200
            r(25, 0, 31, 0, 0x09),          # jalr ra,t9
            i(0x0D, 0, 25, 0x1234),         # ori t9,zero,0x1234 (delay)
            0,
        )
        report = analyze_xrefs(data, target, rom_base=0, vram_base=base, lookback=4)
        self.assertEqual(report["hit_count"], 1)
        hit = report["hits"][0]
        self.assertEqual(hit["call_kind"], "jalr")
        recovered = hit["recovered_indirect_target"]
        self.assertEqual(recovered["source_register"], "t9")
        self.assertEqual(recovered["target"], target)
        self.assertEqual(hit["delay_slot"]["delay_slot_of"], "0x80000008")

    def test_lui_ori_chain_is_preserved_in_provenance(self) -> None:
        base = 0x80000000
        target = 0x80000300
        data = words(
            i(0x0F, 0, 4, 0x8033),
            i(0x0D, 4, 4, 0xB1E0),
            j(0x03, target),
            0,
        )
        report = analyze_xrefs(data, target, rom_base=0, vram_base=base, lookback=4)
        a0 = report["hits"][0]["arguments"]["registers"]["a0"]
        self.assertEqual(a0["value"], 0x8033B1E0)
        self.assertGreaterEqual(len(a0["sources"]), 2)


class SymbolicAbiPropagationTests(unittest.TestCase):
    def test_incoming_arguments_survive_stack_save_calls_and_reload(self) -> None:
        base = 0x80000000
        target = 0x80000400
        other = 0x80000300
        data = words(
            i(0x09, 29, 29, -32),            # addiu sp,sp,-32
            i(0x2B, 29, 31, 28),             # sw ra,28(sp): recognized prologue
            i(0x2B, 29, 4, 32),              # sw a0,32(sp)
            i(0x2B, 29, 5, 36),              # sw a1,36(sp)
            j(0x03, other),                   # jal other
            0,                                # delay
            i(0x23, 29, 14, 48),             # lw t6,48(sp): incoming arg5
            i(0x23, 29, 4, 32),              # lw a0,32(sp)
            i(0x23, 29, 5, 36),              # lw a1,36(sp)
            j(0x03, target),                  # jal target
            i(0x2B, 29, 14, 16),             # sw t6,16(sp): arg5 delay
            0,
        )
        report = analyze_xrefs(data, target, rom_base=0, vram_base=base, lookback=12)
        self.assertEqual(report["hit_count"], 1)
        args = report["hits"][0]["arguments"]
        self.assertEqual(args["registers"]["a0"]["symbol"], "function-entry:a0")
        self.assertEqual(args["registers"]["a1"]["symbol"], "function-entry:a1")
        self.assertEqual(args["stack"]["sp+0x10"]["symbol"], "function-entry:sp+0x10")
        self.assertIsNone(report["hits"][0]["nearest_a0_constant"])


class JalrAdmissionTests(unittest.TestCase):
    def test_symbolic_jalr_target_is_not_admitted_as_concrete_xref(self) -> None:
        base = 0x80000000
        data = words(
            r(4, 0, 31, 0, 0x09),          # jalr ra,a0; incoming a0 is symbolic
            0,
        )
        report = analyze_xrefs(data, 0x80001000, rom_base=0, vram_base=base, lookback=2)
        self.assertEqual(report["hit_count"], 0)


if __name__ == "__main__":
    unittest.main()
