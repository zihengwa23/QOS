import unittest

from qos_scheduler import BatchQuantumScheduler, QuantumJob


class BatchSchedulerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.jobs = [
            QuantumJob("j1", 8, 4),
            QuantumJob("j2", 8, 4),
            QuantumJob("j3", 8, 4),
            QuantumJob("j4", 8, 4),
        ]

    def test_batched_mode_improves_quantum_utilization(self) -> None:
        scheduler = BatchQuantumScheduler(batch_size=2, prep_reuse_factor=0.5)
        naive = scheduler.naive(self.jobs)
        batched = scheduler.batched(self.jobs)

        self.assertGreater(batched.quantum_utilization, naive.quantum_utilization)
        self.assertLess(batched.total_classical_prep_time, naive.total_classical_prep_time)

    def test_pipeline_overlaps_classical_and_quantum_work(self) -> None:
        scheduler = BatchQuantumScheduler(batch_size=2, prep_reuse_factor=1.0)
        result = scheduler.batched(self.jobs)

        first, second = result.timeline[0], result.timeline[1]
        self.assertLess(second.prep_start, first.quantum_end)


if __name__ == "__main__":
    unittest.main()
