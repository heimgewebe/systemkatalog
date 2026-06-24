#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True, help="Scan label for error messages (e.g. 'history', 'tree')")
    parser.add_argument("--return-code", type=int, required=True, help="Gitleaks process return code")
    parser.add_argument("--report", type=Path, required=True, help="Path to the JSON report file")
    args = parser.parse_args()

    label = args.label
    rc = args.return_code

    if rc != 0:
        print(f"FAIL: gitleaks {label} scanner return code: {rc}")
        sys.exit(1)

    if not args.report.exists():
        print(f"FAIL: gitleaks {label} report missing: {args.report}")
        sys.exit(1)

    raw = args.report.read_bytes()
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        print(f"FAIL: gitleaks {label} report is not valid UTF-8: {e}")
        sys.exit(1)

    try:
        data = json.loads(decoded)
    except json.JSONDecodeError as e:
        print(f"FAIL: gitleaks {label} report is invalid JSON: {e}")
        sys.exit(1)

    if not isinstance(data, list):
        print(f"FAIL: gitleaks {label} report type: gefunden={type(data).__name__}, erwartet=array")
        sys.exit(1)

    n = len(data)
    if n != 0:
        print(f"FAIL: gitleaks {label} findings: gefunden={n}, erwartet=0")
        sys.exit(1)

    label_upper = label.upper().replace("-", " ")
    print(f"TARGET-PROOF: GITLEAKS {label_upper} SCAN PASS")


if __name__ == "__main__":
    main()
