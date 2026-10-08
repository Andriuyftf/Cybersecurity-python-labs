import argparse
import json
import logging
import re
import sys
from collections import Counter
from pathlib import Path

log = logging.getLogger(__name__)


def mask(kind, value):
    if kind == "emails":
        name, domain = value.split("@")
        if len(name) == 1:
            return "*@" + domain
        return name[0] + "****" + name[-1] + "@" + domain

    if kind == "cards":
        digits = re.sub(r"\D", "", value)
        return digits[:4] + "-****-****-" + digits[-4:]

    if kind == "phones":
        digits = re.sub(r"\D", "", value)
        result = digits[:3] + "*" * (len(digits) - 5) + digits[-2:]
        if value.startswith("+"):
            result = "+" + result
        return result

    parts = value.split(".")
    return parts[0] + "." + parts[1] + ".*.*"


def main(argv=None):
    parser = argparse.ArgumentParser(description="PII Scanner")
    parser.add_argument("--scan-dir", type=Path, required=True)
    parser.add_argument("--patterns", choices=["all", "cards", "emails"], default="all")
    parser.add_argument("--mask", action="store_true")
    parser.add_argument("--out-json", type=Path, required=True)
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO, format="[%(levelname)s] %(message)s", stream=sys.stdout
    )

    if not args.scan_dir.is_dir():
        log.error("Scan directory does not exist: %s", args.scan_dir)
        return 1

    patterns = {
        "emails": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "cards": r"(?<!\w)[0-9]{4}(?:[ -]?[0-9]{4}){3}(?!\w)",
        "phones": r"(?<![\w+])\+?[0-9](?:[ ()-]*[0-9]){8,14}(?!\w)",
        "ips": r"(?<![\w.])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![\w.])",
    }
    names = {
        "emails": "Email Addresses",
        "cards": "Credit Card Numbers",
        "phones": "Phone Numbers",
        "ips": "IPv4 Addresses",
    }
    labels = {
        "emails": "Email",
        "cards": "Credit Card",
        "phones": "Phone",
        "ips": "IPv4",
    }

    counts = Counter({"emails": 0, "cards": 0, "phones": 0, "ips": 0})
    findings = []
    scanned = 0
    skipped = 0

    log.info("Scanning directory %s for unmasked PII data...", args.scan_dir)

    for file in sorted(args.scan_dir.rglob("*")):
        if not file.is_file() or file.resolve() == args.out_json.resolve():
            continue

        try:
            text = file.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            log.warning("Cannot read file: %s", file)
            skipped += 1
            continue

        if "\x00" in text:
            log.warning("Skipping binary file: %s", file)
            skipped += 1
            continue

        scanned += 1

        for number, line in enumerate(text.splitlines(), 1):
            for kind, pattern in patterns.items():
                if args.patterns != "all" and args.patterns != kind:
                    continue

                search_line = line

                if kind == "phones":
                    search_line = re.sub(patterns["cards"], " ", search_line)
                    search_line = re.sub(
                        r"\b[0-9]{4}-[0-9]{2}-[0-9]{2}\b", " ", search_line
                    )

                for value in re.findall(pattern, search_line):
                    if kind == "ips":
                        valid = True
                        for part in value.split("."):
                            if int(part) > 255 or (len(part) > 1 and part[0] == "0"):
                                valid = False
                        if not valid:
                            continue

                    counts[kind] += 1
                    findings.append(
                        {
                            "file": str(file),
                            "line": number,
                            "type": kind,
                            "value": value,
                        }
                    )

    log.info("Scanned %s files.", scanned)

    print("\n=== Detected Sensitive Data (PII) ===")
    for kind, name in names.items():
        print(f"{name:<19}: {counts[kind]} matches")

    title = "Masked for Display" if args.mask else "Unmasked Display"
    print(f"\n=== Sample Findings ({title}) ===")

    previous = None

    for item in findings[:10]:
        location = (item["file"], item["line"])

        if location != previous:
            print(f"[PII FOUND] File: {item['file']} (Line {item['line']})")
            previous = location

        value = item["value"]

        if args.mask:
            value = mask(item["type"], value)
            if item["type"] == "cards":
                value += " (Original masked)"

        print(f"  {labels[item['type']]:<11} : {value}")

    if not findings:
        print("No sensitive data found.")

    print()

    if findings:
        log.warning("Unmasked PII found in plaintext logs!")

    for item in findings:
        item["" \
        ""] = mask(item["type"], item["value"])

    report = {
        "scan_dir": str(args.scan_dir),
        "patterns": args.patterns,
        "scanned_files": scanned,
        "skipped_files": skipped,
        "counts": dict(counts),
        "findings": findings,
    }

    try:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json.dumps(report, indent=4), encoding="utf-8")
    except OSError:
        log.error("Cannot save report: %s", args.out_json)
        return 1

    log.info("Sanitized report saved to %s", args.out_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())