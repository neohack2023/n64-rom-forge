import inspect
import unittest

from n64rf.emulation.backend import EmulatorBackend


class EmulatorBackendContractTests(unittest.TestCase):
    def test_contract_id_is_frozen(self):
        self.assertEqual(EmulatorBackend.CONTRACT_ID, "N64RF_EMULATOR_BACKEND_01")

    def test_required_capabilities_are_declared(self):
        expected = {
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
        }
        self.assertEqual(set(EmulatorBackend.REQUIRED_CAPABILITIES), expected)

    def test_public_contract_exposes_no_mutation_methods(self):
        denied = {
            "write_memory",
            "write_register",
            "set_pc",
            "inject_code",
            "patch_instruction",
            "modify_rom",
            "alter_asset",
        }
        public_methods = {
            name
            for name, value in inspect.getmembers(EmulatorBackend)
            if callable(value) and not name.startswith("_")
        }
        self.assertTrue(denied.isdisjoint(public_methods), denied & public_methods)


if __name__ == "__main__":
    unittest.main()
