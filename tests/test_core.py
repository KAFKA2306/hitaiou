import os
from pathlib import Path
from tempfile import TemporaryDirectory
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
        with TemporaryDirectory() as directory:
            root = Path(directory)
            older = root / "demand_metrics_20250125_221837.parquet"
            newer = root / "demand_metrics_20250201_010203.parquet"
            older.write_bytes(b"older")
            newer.write_bytes(b"newer")

            os.utime(older, (2_000_000_000, 2_000_000_000))
            os.utime(newer, (1_000_000_000, 1_000_000_000))
            selected, snapshot_id, snapshot_time = server.select_latest_snapshot(
                [older, newer]
            )

            self.assertEqual(selected, newer)
            self.assertEqual(snapshot_id, "20250201_010203")
            self.assertEqual(snapshot_time.isoformat(), "2025-02-01T01:02:03+00:00")

            os.utime(older, (500_000_000, 500_000_000))
            os.utime(newer, (2_100_000_000, 2_100_000_000))
            selected_again, identity_again, time_again = server.select_latest_snapshot(
                [older, newer]
            )
            self.assertEqual(
                (selected_again, identity_again, time_again),
                (selected, snapshot_id, snapshot_time),
            )

    def test_malformed_snapshot_name_fails_closed(self):
        with TemporaryDirectory() as directory:
            malformed = Path(directory) / "demand_metrics_latest.parquet"
            malformed.write_bytes(b"invalid")
            with self.assertRaisesRegex(ValueError, "Malformed dashboard snapshot name"):
                server.select_latest_snapshot([malformed])

    def test_invalid_snapshot_time_fails_closed(self):
        with TemporaryDirectory() as directory:
            invalid = Path(directory) / "demand_metrics_20250230_010203.parquet"
            invalid.write_bytes(b"invalid")
            with self.assertRaisesRegex(ValueError, "Invalid dashboard snapshot time"):
                server.select_latest_snapshot([invalid])

    def test_duplicate_snapshot_identity_is_rejected(self):
        class SnapshotPath:
            def __init__(self, name):
                self.name = name

        first = SnapshotPath("demand_metrics_20250201_010203.parquet")
        second = SnapshotPath("demand_metrics_20250201_010203.parquet")
        with self.assertRaisesRegex(ValueError, "Ambiguous dashboard snapshot identity"):
            server.select_latest_snapshot([first, second])


if __name__ == "__main__":
    unittest.main()
