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


if __name__ == "__main__":
    unittest.main()
