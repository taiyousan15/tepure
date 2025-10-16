#!/usr/bin/env python3
"""
Secrets Preflight Checker

Usage:
    # Check environment variables
    python ops/check-secrets.py --source env --json

    # Check .env file
    python ops/check-secrets.py --source file --file .env --json

Exit codes:
    0: All required secrets present and valid
    1: Missing required secrets or validation errors
    2: Command line argument error
"""

import os
import sys
import json
import argparse
import re
from typing import List, Tuple, Dict


def load_required_keys(path: str) -> Tuple[List[str], List[str]]:
    """
    Load required and optional keys from .env.required file

    Returns:
        Tuple of (required_keys, optional_keys)
    """
    required = []
    optional = []

    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()

                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue

                # Optional keys end with ?
                if line.endswith("?"):
                    optional.append(line[:-1])
                else:
                    required.append(line)
    except FileNotFoundError:
        print(f"ERROR: Required file not found: {path}", file=sys.stderr)
        sys.exit(2)

    return required, optional


def parse_env_file(path: str) -> Dict[str, str]:
    """Parse .env file and return dict of key=value pairs"""
    env = {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()

                # Skip comments and lines without =
                if line.startswith("#") or "=" not in line:
                    continue

                # Split on first = only
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip()
    except FileNotFoundError:
        print(f"ERROR: .env file not found: {path}", file=sys.stderr)
        sys.exit(2)

    return env


def is_nonempty(value: str) -> bool:
    """Check if value is not empty"""
    return value is not None and len(value.strip()) > 0


def validate_formats(env: Dict[str, str]) -> List[Dict[str, str]]:
    """
    Validate environment variable formats

    Returns:
        List of validation issues
    """
    issues = []

    # Validate GOOGLE_SERVICE_ACCOUNT_JSON_BASE64
    if "GOOGLE_SERVICE_ACCOUNT_JSON_BASE64" in env and is_nonempty(env.get("GOOGLE_SERVICE_ACCOUNT_JSON_BASE64", "")):
        b64_value = env["GOOGLE_SERVICE_ACCOUNT_JSON_BASE64"]

        # Check if it looks like base64
        if not re.fullmatch(r"[A-Za-z0-9+/=]+", b64_value):
            issues.append({
                "key": "GOOGLE_SERVICE_ACCOUNT_JSON_BASE64",
                "reason": "not-base64-like",
                "hint": "Should contain only A-Z, a-z, 0-9, +, /, ="
            })

    # Validate ERROR_RATE_THRESHOLD (should be 0-1)
    if "ERROR_RATE_THRESHOLD" in env and is_nonempty(env.get("ERROR_RATE_THRESHOLD", "")):
        try:
            threshold = float(env["ERROR_RATE_THRESHOLD"])
            if not (0.0 < threshold < 1.0):
                issues.append({
                    "key": "ERROR_RATE_THRESHOLD",
                    "reason": "should-be-0to1",
                    "hint": "Valid range: 0.0 < value < 1.0 (e.g., 0.05 for 5%)"
                })
        except ValueError:
            issues.append({
                "key": "ERROR_RATE_THRESHOLD",
                "reason": "not-float",
                "hint": "Should be a float number (e.g., 0.05)"
            })

    # Validate LATENCY_P95_THRESHOLD_MS (should be positive integer)
    if "LATENCY_P95_THRESHOLD_MS" in env and is_nonempty(env.get("LATENCY_P95_THRESHOLD_MS", "")):
        try:
            latency = int(env["LATENCY_P95_THRESHOLD_MS"])
            if latency <= 0:
                issues.append({
                    "key": "LATENCY_P95_THRESHOLD_MS",
                    "reason": "should-be-positive",
                    "hint": "Should be positive integer (e.g., 2000 for 2000ms)"
                })
        except ValueError:
            issues.append({
                "key": "LATENCY_P95_THRESHOLD_MS",
                "reason": "not-integer",
                "hint": "Should be an integer (e.g., 2000)"
            })

    # Validate DAILY_COST_THRESHOLD_USD (should be positive float)
    if "DAILY_COST_THRESHOLD_USD" in env and is_nonempty(env.get("DAILY_COST_THRESHOLD_USD", "")):
        try:
            cost = float(env["DAILY_COST_THRESHOLD_USD"])
            if cost <= 0:
                issues.append({
                    "key": "DAILY_COST_THRESHOLD_USD",
                    "reason": "should-be-positive",
                    "hint": "Should be positive number (e.g., 50.0 for $50/day)"
                })
        except ValueError:
            issues.append({
                "key": "DAILY_COST_THRESHOLD_USD",
                "reason": "not-float",
                "hint": "Should be a number (e.g., 50.0)"
            })

    return issues


def main():
    parser = argparse.ArgumentParser(
        description="Check required secrets/environment variables",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--required-file",
        default="ops/.env.required",
        help="Path to .env.required file (default: ops/.env.required)"
    )

    parser.add_argument(
        "--source",
        choices=["env", "file"],
        default="env",
        help="Source of environment variables (env: process env, file: .env file)"
    )

    parser.add_argument(
        "--file",
        help="Path to .env file (required when --source file)"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format (machine-readable)"
    )

    args = parser.parse_args()

    # Load required and optional keys
    required_keys, optional_keys = load_required_keys(args.required_file)

    # Get environment variables
    if args.source == "env":
        # Read from process environment
        env = {k: os.environ.get(k, "") for k in set(required_keys + optional_keys)}
    elif args.source == "file":
        if not args.file:
            print("ERROR: --file is required when --source file", file=sys.stderr)
            sys.exit(2)

        # Read from .env file
        env = parse_env_file(args.file)

    # Check for missing required keys
    missing = [k for k in required_keys if not is_nonempty(env.get(k, ""))]

    # Check for missing optional keys (warnings only)
    warnings = [k for k in optional_keys if not is_nonempty(env.get(k, ""))]

    # Validate formats
    format_issues = validate_formats(env)

    # Determine overall status
    ok = (len(missing) == 0 and len(format_issues) == 0)

    # Build result
    result = {
        "ok": ok,
        "missing": missing,
        "warnings": warnings,
        "format_issues": format_issues,
        "checked": sorted(list(set(required_keys + optional_keys)))
    }

    # Output
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if ok:
            print("✅ Secrets OK")
            print(f"   Checked {len(result['checked'])} keys")

        if missing:
            print(f"❌ Missing required keys ({len(missing)}):")
            for key in missing:
                print(f"   - {key}")

        if warnings:
            print(f"⚠️  Optional keys missing ({len(warnings)}):")
            for key in warnings:
                print(f"   - {key}")

        if format_issues:
            print(f"⚠️  Format validation issues ({len(format_issues)}):")
            for issue in format_issues:
                print(f"   - {issue['key']}: {issue['reason']}")
                if 'hint' in issue:
                    print(f"     Hint: {issue['hint']}")

    # Exit with appropriate code
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
