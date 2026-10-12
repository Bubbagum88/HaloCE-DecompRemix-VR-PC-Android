"""Focused package metadata regression gate; no builds/signing/network needed."""
import ast
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("package_quest", ROOT / "tools/package-quest.py")
package = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package)


class CandidateMetadataTests(unittest.TestCase):
    def test_current_handoff_prefix(self):
        expected = ["TEST62-DELIVERY-STATUS.md", "TEST62-CHECKLIST.md",
                    "TEST62-FIELD-GUIDE.md", "TEST62-DEVICE-CHECKLIST.md"]
        for label in ("test62", "test62b"):
            self.assertEqual(package.candidate_document_prefix(label), expected)
        # Test63: its own handoff first, then Test62's
        current = ["TEST63-DELIVERY-STATUS.md", "TEST63-CHECKLIST.md",
                   "TEST63-FIELD-GUIDE.md", "TEST63-DEVICE-CHECKLIST.md"]
        for label in ("test63", "test64"):
            self.assertEqual(package.candidate_document_prefix(label), current + expected)
        for name in current:
            self.assertTrue((ROOT / "docs" / name).is_file())
        for name in expected:
            self.assertTrue((ROOT / "docs" / name).is_file())
        for label in ("test51", "test61", "1.0.19"):
            self.assertEqual(package.candidate_document_prefix(label), [])

    def test_native_default_from_exact_runtime_source(self):
        native = (ROOT / "port/linux/src/port_config.c").read_text()
        with patch.object(package.subprocess, "check_output", return_value=native) as read:
            self.assertEqual(package.client_default_target("test62", "runtime-commit"), 0)
            self.assertEqual(read.call_args.args[0],
                             ["git", "show", "runtime-commit:port/linux/src/port_config.c"])
        for number in (0, 24, 28):
            source = '{ "network.protocol_version", _config_integer, "%d", 0 },' % number
            with patch.object(package.subprocess, "check_output", return_value=source):
                self.assertEqual(package.client_default_target("test53", "abc"), number)

    def test_missing_ambiguous_or_malformed_default_fails_closed(self):
        declaration = '{ "network.protocol_version", _config_integer, "0", 0 },'
        for source in ("", declaration + "\n" + declaration,
                       declaration.replace('"0"', '"auto"'),
                       declaration.replace('_config_integer', '_config_string')):
            with patch.object(package.subprocess, "check_output", return_value=source):
                with self.assertRaises(SystemExit):
                    package.client_default_target("test62", "abc")

    def test_older_release_metadata_preserved(self):
        with patch.object(package.subprocess, "check_output") as read:
            for label in ("test37", "test51", "test52", "1.0.18", "1.0.19"):
                self.assertEqual(package.client_default_target(label, "abc"), 24)
            read.assert_not_called()

    def test_helpers_are_wired_into_manifest_and_document_copy(self):
        tree = ast.parse((ROOT / "tools/package-quest.py").read_text())
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        manifest = next(node.value for node in main.body if isinstance(node, ast.Assign)
                        and any(isinstance(target, ast.Name) and target.id == "manifest" for target in node.targets))
        target = next(value for key, value in zip(manifest.keys, manifest.values)
                      if isinstance(key, ast.Constant) and key.value == "client_default_target")
        self.assertIsInstance(target, ast.Call)
        self.assertEqual(target.func.id, "client_default_target")
        statements = [ast.unparse(node) for node in main.body]
        prefix = "active_candidate_docs = candidate_document_prefix(args.label) + active_candidate_docs"
        self.assertIn(prefix, statements)
        prefix_index = statements.index(prefix)
        documents_index = next(i for i, item in enumerate(statements) if item.startswith("documents = edition_docs"))
        self.assertLess(prefix_index, documents_index)


if __name__ == "__main__":
    unittest.main()
