import os
from pathlib import Path
import tempfile
import unittest

import server
from process import DataProcessor


class CoreContractTests(unittest.TestCase):
    def test_booth_item_url_parsing(self):
        self.assertEqual(
            DataProcessor.extract_booth_info("https://example.booth.pm/items/123456"),
            ("example", "123456"),
        )
        self.assertEqual(
            DataProcessor.extract_booth_info("https://booth.pm/ja/items/987654"),
            (None, "987654"),
        )

    def test_server_has_single_main_entrypoint(self):
        self.assertTrue(callable(server.main))
        self.assertTrue(hasattr(server, "DashboardHandler"))

    def test_latest_snapshot_uses_semantic_identity_not_mtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            older = root / "demand_metrics_20250101_120000.parquet"
            newer = root / "demand_metrics_20250102_120000.parquet"
            older.write_bytes(b"older")
            newer.write_bytes(b"newer")

            os.utime(older, (2_000_000_000, 2_000_000_000))
            os.utime(newer, (1_000_000_000, 1_000_000_000))

            selected, snapshot_id, observed_at = server.select_latest_snapshot(root)
            self.assertEqual(selected, newer)
            self.assertEqual(snapshot_id, "20250102_120000")
            self.assertEqual(observed_at.isoformat(), "2025-01-02T12:00:00+00:00")

            os.utime(older, (500_000_000, 500_000_000))
            os.utime(newer, (2_100_000_000, 2_100_000_000))
            selected_again, snapshot_id_again, observed_at_again = (
                server.select_latest_snapshot(root)
            )
            self.assertEqual(selected_again, selected)
            self.assertEqual(snapshot_id_again, snapshot_id)
            self.assertEqual(observed_at_again, observed_at)

    def test_malformed_snapshot_identity_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "demand_metrics_20250102_120000.parquet").write_bytes(b"ok")
            (root / "demand_metrics_latest.parquet").write_bytes(b"bad")

            with self.assertRaisesRegex(
                ValueError, "Invalid demand metrics snapshot name"
            ):
                server.select_latest_snapshot(root)

    def test_tracked_snapshot_identity_is_readable(self):
        path = Path("data/dashboard/demand_metrics_20250125_221837.parquet")
        snapshot_id, observed_at = server.snapshot_identity(path)
        self.assertEqual(snapshot_id, "20250125_221837")
        self.assertEqual(observed_at.isoformat(), "2025-01-25T22:18:37+00:00")


if __name__ == "__main__":
    unittest.main()
