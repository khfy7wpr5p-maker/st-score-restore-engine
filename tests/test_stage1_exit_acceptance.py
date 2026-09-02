from __future__ import annotations

import unittest

from tools.validate_stage1_exit_acceptance import validate


class Stage1ExitAcceptanceTests(unittest.TestCase):
    def test_stage1_exit_acceptance_is_internally_consistent(self) -> None:
        self.assertEqual(validate(), [])


if __name__ == "__main__":
    unittest.main()
