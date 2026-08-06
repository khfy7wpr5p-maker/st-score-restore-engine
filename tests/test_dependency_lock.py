from __future__ import annotations

import unittest

from tools.validate_dependency_lock import parse_hashed_pins


class DependencyLockTests(unittest.TestCase):
    def test_validation_dependency_requires_hash(self) -> None:
        with self.assertRaises(SystemExit):
            parse_hashed_pins(["attrs==26.1.0"], "test.lock")

    def test_validation_dependency_rejects_malformed_hash(self) -> None:
        with self.assertRaises(SystemExit):
            parse_hashed_pins(
                ["attrs==26.1.0 --hash=sha256:not-a-digest"], "test.lock"
            )

    def test_validation_dependency_rejects_duplicate_hash(self) -> None:
        digest = "a" * 64
        with self.assertRaises(SystemExit):
            parse_hashed_pins(
                [
                    "attrs==26.1.0 "
                    f"--hash=sha256:{digest} --hash=sha256:{digest}"
                ],
                "test.lock",
            )

    def test_validation_dependency_accepts_multiple_platform_hashes(self) -> None:
        first, second = "a" * 64, "b" * 64
        pins, hashes = parse_hashed_pins(
            [
                "rpds-py==2026.5.1 "
                f"--hash=sha256:{first} --hash=sha256:{second}"
            ],
            "test.lock",
        )
        self.assertEqual(pins, {"rpds-py": "2026.5.1"})
        self.assertEqual(hashes, {"rpds-py": {first, second}})


if __name__ == "__main__":
    unittest.main()
