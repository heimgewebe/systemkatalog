#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import socket
import subprocess
import sys
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/serve_system_catalog.py"

spec = importlib.util.spec_from_file_location("system_catalog_service", SCRIPT)
assert spec and spec.loader
service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(service)


class SystemCatalogServiceTests(unittest.TestCase):
    def test_payload_is_composed_from_canonical_inputs(self) -> None:
        payload = service.build_catalog_payload()
        self.assertEqual(payload["kind"], "heimgewebe_system_catalog")
        self.assertEqual(len(payload["systems"]), 19)
        self.assertEqual(len(payload["relations"]), 24)
        self.assertEqual(len(payload["truthOwnership"]), 14)
        self.assertNotIn("runtimeHealth", payload)
        self.assertNotIn("taskState", payload)

    def test_html_is_readable_and_escapes_values(self) -> None:
        payload = service.build_catalog_payload()
        payload["systems"] = [
            {"id": "x", "label": "<script>", "kind": "repository", "purpose": "safe & stable"}
        ]
        rendered = service.render_html(payload).decode()
        self.assertIn("Heimgewebe-Systemkatalog", rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertNotIn("<script>", rendered)

    def test_check_mode_and_loopback_gate(self) -> None:
        ok = subprocess.run(
            [sys.executable, str(SCRIPT), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertTrue(json.loads(ok.stdout)["valid"])
        blocked = subprocess.run(
            [sys.executable, str(SCRIPT), "--bind", "0.0.0.0", "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn("loopback", blocked.stderr)

    def test_live_http_surface_is_read_only(self) -> None:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        process = subprocess.Popen(
            [sys.executable, str(SCRIPT), "--port", str(port)],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            base = f"http://127.0.0.1:{port}"
            for _ in range(40):
                try:
                    with urllib.request.urlopen(base + "/healthz", timeout=0.2) as response:
                        if response.status == 204:
                            break
                except OSError:
                    time.sleep(0.05)
            else:
                self.fail("service did not start")
            with urllib.request.urlopen(base + "/api/catalog.json", timeout=2) as response:
                payload = json.load(response)
                self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
            self.assertEqual(payload["kind"], "heimgewebe_system_catalog")
            with urllib.request.urlopen(base + "/", timeout=2) as response:
                self.assertIn(b"Heimgewebe-Systemkatalog", response.read())
            request = urllib.request.Request(base + "/api/catalog.json", data=b"{}", method="POST")
            with self.assertRaises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(request, timeout=2)
            self.assertEqual(caught.exception.code, 405)
        finally:
            process.terminate()
            process.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
