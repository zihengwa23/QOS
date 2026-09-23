from __future__ import annotations

from pathlib import Path
import unittest

from qos.config import load_config
from qos.experiment import run_experiment


class ExperimentTest(unittest.TestCase):
    def test_experiment_outputs_expected_structure(self) -> None:
        config_path = Path(__file__).resolve().parents[1] / "configs" / "toolchain_baseline.json"
        config = load_config(str(config_path))
        result = run_experiment(config)

        self.assertIn("results", result)
        self.assertIn("default", result["results"])
        self.assertIn("qos", result["results"])
        self.assertIn("comparison", result)
        self.assertIn("toolchain", result)
        self.assertEqual(result["toolchain"]["compiler"], "QLLVM")
        self.assertGreater(result["results"]["default"]["total_jobs"], 0)
        self.assertGreaterEqual(result["results"]["qos"]["success_rate"], 0.0)
        self.assertLessEqual(result["results"]["qos"]["success_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()

