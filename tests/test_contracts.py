from __future__ import annotations

import json, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from n64rf.adapters.goldeneye import GOLDENEYE_007_US
from n64rf.adapters.sm64 import SM64_US
from n64rf.receipts import ExecutionReceipt
from n64rf.rom_inspector import detect_byte_order, normalize_to_z64

class ContractTests(unittest.TestCase):
    def test_json_schemas_parse(self) -> None:
        for path in sorted((ROOT / "schemas").glob("*.json")):
            with path.open("r", encoding="utf-8") as f: parsed = json.load(f)
            self.assertEqual(parsed["type"], "object")
    def test_sm64_adapter_accepts_only_frozen_us_identity(self) -> None:
        self.assertTrue(SM64_US.accepts("9bef1128717f958171a4afac3ed78ee2bb4e86ce", "z64")); self.assertFalse(SM64_US.accepts("0" * 40, "z64")); self.assertFalse(SM64_US.accepts("9bef1128717f958171a4afac3ed78ee2bb4e86ce", "v64"))
    def test_goldeneye_adapter_is_canonical_prefix(self) -> None:
        candidate = GOLDENEYE_007_US.accepted_inputs[0]; self.assertEqual(candidate.canonical_rule, "canonical-prefix"); self.assertEqual(candidate.size_bytes, 12582912); self.assertEqual(candidate.sha1, "abe01e4aeb033b6c0836819f549c791b26cfde83")
    def test_byte_order_magic_and_normalization(self) -> None:
        self.assertEqual(detect_byte_order(bytes.fromhex("80371240")), "z64"); self.assertEqual(detect_byte_order(bytes.fromhex("37804012")), "v64"); self.assertEqual(detect_byte_order(bytes.fromhex("40123780")), "n64"); self.assertEqual(normalize_to_z64(bytes.fromhex("37804012"), "v64"), bytes.fromhex("80371240"))
    def test_execution_receipt_defaults_to_not_run(self) -> None:
        receipt = ExecutionReceipt(schema="n64rf.execution-receipt.v1", plan_id="MASON-20260902-N64RF-PHASE0-SUBSTRATE-01", plan_digest="SHA256:bb66563dbf1871a433967807adf77d9f97780a8f755624c17e880a2916402fd8", repository="neohack2023/n64-rom-forge", branch="feature/rom-wrapper-backend-01"); self.assertEqual(receipt.phase0_state, "NOT_RUN")

if __name__ == "__main__": unittest.main()
