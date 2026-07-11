#!/usr/bin/env python3
"""Read-only HTTP projection for the Heimgewebe system catalog."""

from __future__ import annotations

import argparse
import html
import json
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[1]
LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}
ROUTES = {
    "/catalog.md": ("rendered/system-catalog.md", "text/markdown; charset=utf-8"),
    "/README.md": ("README.md", "text/markdown; charset=utf-8"),
    "/AGENTS.md": ("AGENTS.md", "text/markdown; charset=utf-8"),
    "/map.mmd": ("rendered/ecosystem-registry-map.mmd", "text/plain; charset=utf-8"),
    "/api/nodes.json": ("registry/ecosystem/nodes.json", "application/json; charset=utf-8"),
    "/api/edges.json": ("registry/ecosystem/edges.json", "application/json; charset=utf-8"),
    "/api/authority-matrix.json": (
        "registry/ecosystem/authority-matrix.v1.json",
        "application/json; charset=utf-8",
    ),
    "/api/policy.json": ("policy/system-catalog.v1.json", "application/json; charset=utf-8"),
}


def _load_json(relative: str) -> dict[str, Any]:
    value = json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{relative} must contain a JSON object")
    return value


def build_catalog_payload() -> dict[str, Any]:
    nodes = _load_json("registry/ecosystem/nodes.json")
    edges = _load_json("registry/ecosystem/edges.json")
    authority = _load_json("registry/ecosystem/authority-matrix.v1.json")
    policy = _load_json("policy/system-catalog.v1.json")
    return {
        "schemaVersion": 1,
        "kind": "heimgewebe_system_catalog",
        "title": "Heimgewebe-Systemkatalog",
        "role": policy["role"],
        "systems": nodes["nodes"],
        "relations": edges["edges"],
        "truthOwnership": authority["authorities"],
        "entrypoints": policy["entrypoints"],
        "doesNotAnswer": policy["doesNotAnswer"],
        "doesNotEstablish": policy["doesNotEstablish"],
    }


def _link(target: str, label: str | None = None) -> str:
    escaped_target = html.escape(target, quote=True)
    escaped_label = html.escape(label or target)
    return f'<a href="{escaped_target}">{escaped_label}</a>'


def render_html(payload: dict[str, Any]) -> bytes:
    systems = sorted(payload["systems"], key=lambda item: str(item["label"]).casefold())
    relations = sorted(
        payload["relations"],
        key=lambda item: (str(item["from"]), str(item["type"]), str(item["to"])),
    )
    authorities = sorted(payload["truthOwnership"], key=lambda item: str(item["domain"]))
    entrypoints = payload["entrypoints"]

    system_rows = "".join(
        "<tr>"
        f"<td><code>{html.escape(str(item['id']))}</code></td>"
        f"<td><strong>{html.escape(str(item['label']))}</strong></td>"
        f"<td>{html.escape(str(item['kind']))}</td>"
        f"<td>{html.escape(str(item['purpose']))}</td>"
        "</tr>"
        for item in systems
    )
    authority_rows = "".join(
        "<tr>"
        f"<td><code>{html.escape(str(item['domain']))}</code></td>"
        f"<td><code>{html.escape(str(item['owner']))}</code></td>"
        f"<td>{html.escape(', '.join(item.get('projections', [])) or '—')}</td>"
        "</tr>"
        for item in authorities
    )
    relation_rows = "".join(
        "<tr>"
        f"<td><code>{html.escape(str(item['from']))}</code></td>"
        f"<td><code>{html.escape(str(item['type']))}</code></td>"
        f"<td><code>{html.escape(str(item['to']))}</code></td>"
        f"<td>{html.escape(str(item['stability']))}</td>"
        f"<td>{html.escape(str(item['meaning']))}</td>"
        "</tr>"
        for item in relations
    )
    entrypoint_items = "".join(
        f"<li>{_link(str(item['target']), str(item['label']))}</li>" for item in entrypoints
    )
    non_answers = "".join(
        f"<li><code>{html.escape(str(value))}</code></li>" for value in payload["doesNotAnswer"]
    )

    document = f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Heimgewebe-Systemkatalog</title>
<style>
:root {{ color-scheme: dark; --bg:#111315; --panel:#1a1d21; --line:#343941; --text:#eceff4; --muted:#aeb6c2; --accent:#8bc5ff; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--text); font:16px/1.5 system-ui,sans-serif; }}
main {{ width:min(1180px,94vw); margin:0 auto; padding:3rem 0 5rem; }}
header {{ margin-bottom:2rem; }}
h1 {{ font-size:clamp(2rem,5vw,4rem); margin:.2rem 0; }}
h2 {{ margin-top:2.4rem; }}
p,li {{ color:var(--muted); }}
a {{ color:var(--accent); }}
nav {{ display:flex; flex-wrap:wrap; gap:.8rem 1.2rem; padding:1rem; background:var(--panel); border:1px solid var(--line); border-radius:14px; }}
section {{ overflow:auto; }}
table {{ width:100%; border-collapse:collapse; background:var(--panel); border:1px solid var(--line); }}
th,td {{ padding:.75rem; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }}
th {{ position:sticky; top:0; background:#22262c; }}
code {{ color:#d6e8ff; }}
.badge {{ display:inline-block; padding:.2rem .55rem; border:1px solid var(--line); border-radius:999px; color:var(--muted); }}
</style>
</head>
<body><main>
<header>
<span class="badge">read-only · app-unabhängig · kein Live-Status</span>
<h1>Heimgewebe-Systemkatalog</h1>
<p>Stabile Systeme, Zwecke, Wahrheitszuständigkeiten, Beziehungen und Einstiegspunkte.</p>
</header>
<nav>
<a href="/api/catalog.json">Katalog JSON</a>
<a href="/catalog.md">Markdown</a>
<a href="/map.mmd">Mermaid</a>
<a href="/api/authority-matrix.json">Authority Matrix</a>
<a href="/api/policy.json">Policy</a>
</nav>
<h2>Systeme</h2>
<section><table><thead><tr><th>ID</th><th>Name</th><th>Typ</th><th>Zweck</th></tr></thead><tbody>{system_rows}</tbody></table></section>
<h2>Wahrheitszuständigkeiten</h2>
<section><table><thead><tr><th>Domäne</th><th>Primärquelle</th><th>Projektionen</th></tr></thead><tbody>{authority_rows}</tbody></table></section>
<h2>Stabile Beziehungen</h2>
<section><table><thead><tr><th>Von</th><th>Beziehung</th><th>Zu</th><th>Klasse</th><th>Bedeutung</th></tr></thead><tbody>{relation_rows}</tbody></table></section>
<h2>Einstiegspunkte</h2><ul>{entrypoint_items}</ul>
<h2>Nicht Aufgabe dieses Katalogs</h2><ul>{non_answers}</ul>
</main></body></html>"""
    return document.encode("utf-8")


class CatalogHandler(BaseHTTPRequestHandler):
    server_version = "HeimgewebeSystemkatalog/1"

    def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; img-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _dispatch(self) -> None:
        path = urlsplit(self.path).path
        try:
            if path == "/healthz":
                self.send_response(HTTPStatus.NO_CONTENT)
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                return
            payload = build_catalog_payload()
            if path == "/":
                self._send(HTTPStatus.OK, render_html(payload), "text/html; charset=utf-8")
                return
            if path == "/api/catalog.json":
                body = (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
                self._send(HTTPStatus.OK, body, "application/json; charset=utf-8")
                return
            route = ROUTES.get(path)
            if route:
                relative, content_type = route
                body = (REPO_ROOT / relative).read_bytes()
                self._send(HTTPStatus.OK, body, content_type)
                return
            self._send(HTTPStatus.NOT_FOUND, b"not found\n", "text/plain; charset=utf-8")
        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            self._send(HTTPStatus.INTERNAL_SERVER_ERROR, b"catalog unavailable\n", "text/plain; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        self._dispatch()

    def do_HEAD(self) -> None:  # noqa: N802
        self._dispatch()

    def do_POST(self) -> None:  # noqa: N802
        self._send(HTTPStatus.METHOD_NOT_ALLOWED, b"read only\n", "text/plain; charset=utf-8")

    def log_message(self, format: str, *args: object) -> None:
        print(f"systemkatalog: {self.address_string()} {format % args}", file=sys.stderr)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4001)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.bind not in LOOPBACK_HOSTS:
        raise SystemExit("bind address must be loopback")
    if not 1 <= args.port <= 65535:
        raise SystemExit("port must be between 1 and 65535")
    payload = build_catalog_payload()
    rendered = render_html(payload)
    if args.check:
        print(
            json.dumps(
                {
                    "valid": True,
                    "systems": len(payload["systems"]),
                    "relations": len(payload["relations"]),
                    "truthOwnership": len(payload["truthOwnership"]),
                    "htmlBytes": len(rendered),
                },
                sort_keys=True,
            )
        )
        return 0
    server = ThreadingHTTPServer((args.bind, args.port), CatalogHandler)
    server.daemon_threads = True
    print(f"Heimgewebe-Systemkatalog auf http://{args.bind}:{args.port}", file=sys.stderr)
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
