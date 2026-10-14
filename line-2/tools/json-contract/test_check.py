"""Offline regression suite. Run from the repository root with the README command."""
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("checker", HERE / "check.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class Contracts(unittest.TestCase):
    def check(self, value, contract):
        return checker.validate(value, checker.prepare(contract))

    def test_example_report(self):
        c = checker.load(str(HERE / "report.contract.json"))
        doc = checker.load(str(HERE / "report.example.json"))
        self.assertEqual(self.check(doc, c), [])
        doc["checks"][0]["passed"] = "yes"
        doc["checks"][0]["seconds"] = -1
        doc["extra"] = 5
        errors = self.check(doc, c)
        self.assertEqual({e["path"] for e in errors},
                         {"/checks/0/passed", "/checks/0/seconds", "/extra"})

    def test_real_existing_record(self):
        self.assertEqual(self.check(checker.load("dist/line-1/01.json"),
                                    checker.load(str(HERE / "record.contract.json"))), [])

    def test_types(self):
        good = {"integer": 1, "number": 1.5, "boolean": True, "null": None,
                "object": {}, "array": [], "string": "hello"}
        for typ, value in good.items():
            with self.subTest(typ=typ):
                self.assertFalse(self.check(value, {"type": typ}))
                self.assertTrue(self.check("wrong" if typ != "string" else 1,
                                           {"type": typ}))
        self.assertTrue(self.check(True, {"type": "integer"}))
        self.assertTrue(self.check(False, {"type": "number"}))
        self.assertTrue(self.check(1.0, {"type": "integer"}))

    def test_enum_boolean_not_number(self):
        self.assertTrue(self.check(True, {"type": "boolean", "enum": [1]}))
        self.assertTrue(self.check([True], {"type": "array", "enum": [[1]]}))
        self.assertTrue(self.check({"x": True}, {"type": "object", "enum": [{"x": 1}]}))
        self.assertFalse(self.check(1.0, {"type": "number", "enum": [1]}))

    def test_lengths_and_pattern(self):
        c = {"type": "string", "minLength": 2, "maxLength": 3, "pattern": "^[a-z]+$"}
        self.assertFalse(self.check("abc", c))
        self.assertTrue(self.check("a", c))
        self.assertTrue(self.check("abcd", c))
        self.assertTrue(self.check("AB", c))
        self.assertFalse(self.check([1], {"type": "array", "minItems": 1, "maxItems": 1}))
        self.assertTrue(self.check([], {"type": "array", "minItems": 1}))
        self.assertTrue(self.check([1, 2], {"type": "array", "maxItems": 1}))

    def test_boundaries(self):
        c = {"type": "number", "minimum": 0, "maximum": 10}
        for v in (0, 10):
            self.assertFalse(self.check(v, c))
        for v in (-0.01, 10.01):
            self.assertTrue(self.check(v, c))

    def test_pointer_escaping(self):
        c = {"type": "object", "required": ["a/b~c"],
             "properties": {"a/b~c": {"type": "null"}}}
        self.assertEqual(self.check({}, c)[0]["path"], "/a~1b~0c")
        self.assertEqual(self.check("x", {"type": "integer"})[0]["path"], "")

    def test_invalid_contracts_fail_closed(self):
        cases = [{"type": "string", "minLenght": 4},
                 {"type": "oops"}, {"type": []},
                 {"type": "object", "properties": []},
                 {"type": "object", "required": ["missing"]},
                 {"type": "object", "additionalProperties": 1},
                 {"type": "string", "pattern": "["},
                 {"type": "string", "minLength": -1},
                 {"type": "array", "minItems": True},
                 {"type": "array", "minItems": 3, "maxItems": 2},
                 {"type": "integer", "minimum": float("inf")},
                 {"type": "boolean", "minimum": 0},
                 {"type": "array", "items": {}},
                 {"type": "string", "enum": []}]
        for c in cases:
            with self.subTest(c=c), self.assertRaises(checker.ContractError):
                checker.prepare(c)

    def test_refuses_outside_and_hidden_paths(self):
        for p in ("/etc/passwd", "../escape.json", ".git/config"):
            with self.subTest(p=p), self.assertRaises(ValueError):
                checker.workspace_file(p)

    def test_cli_success_and_input_error(self):
        result = subprocess.run([sys.executable, str(HERE / "check.py"),
                                 str(HERE / "report.contract.json"),
                                 str(HERE / "report.example.json")],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(json.loads(result.stdout)["valid"])
        result = subprocess.run([sys.executable, str(HERE / "check.py"),
                                 str(HERE / "report.contract.json"), "/etc/passwd"],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("error", json.loads(result.stdout))


if __name__ == "__main__":
    unittest.main(verbosity=2)
