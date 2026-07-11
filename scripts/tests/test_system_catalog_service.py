from __future__ import annotations

import json
import sys
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from serve_system_catalog import CatalogHandler, build_catalog_payload, render_html  # noqa: E402


class SystemCatalogServiceTests(unittest.TestCase):
    def test_payload_has_neutral_identity(self) -> None:
        payload = build_catalog_payload()
        self.assertEqual(payload["kind"], "system_catalog")
        self.assertEqual(payload["title"], "Systemkatalog")
        self.assertEqual(len(payload["systems"]), 19)
        self.assertEqual(len(payload["relations"]), 24)
        self.assertEqual(len(payload["truthOwnership"]), 14)

    def test_html_is_read_only_catalog(self) -> None:
        rendered = render_html(build_catalog_payload()).decode("utf-8")
        self.assertIn("<h1>Systemkatalog</h1>", rendered)
        self.assertIn("read-only", rendered)
        self.assertNotIn("Heimgewebe-Systemkatalog", rendered)

    def test_http_routes_and_write_rejection(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), CatalogHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            with urllib.request.urlopen(base + "/healthz") as response:
                self.assertEqual(response.status, 204)
            with urllib.request.urlopen(base + "/api/catalog.json") as response:
                payload = json.load(response)
                self.assertEqual(payload["kind"], "system_catalog")
            with urllib.request.urlopen(base + "/") as response:
                self.assertIn(b"Systemkatalog", response.read())
            request = urllib.request.Request(base + "/", method="POST", data=b"{}")
            with self.assertRaises(urllib.error.HTTPError) as raised:
                urllib.request.urlopen(request)
            self.assertEqual(raised.exception.code, 405)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
