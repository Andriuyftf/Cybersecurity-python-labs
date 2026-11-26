import argparse
import json
import re
import sys
from pathlib import Path

from labs.lab04 import analysis, api_client
from shared.student import VARIANT_NUMBER


def load_response(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cve", required=True)
    parser.add_argument("--input", type=Path)
    args = parser.parse_args(argv)

    if not re.fullmatch(r"CVE-[0-9]{4}-[0-9]{4,}", args.cve):
        parser.error("--cve має відповідати формату CVE-YYYY-NNNN.")
    if type(VARIANT_NUMBER) is not int or not 1 <= VARIANT_NUMBER <= 15:
        print("Номер варіанта має бути цілим числом від 1 до 15.", file=sys.stderr)
        return 2

    try:
        if args.input is None:
            payload = api_client.fetch_response(args.cve)
        else:
            payload = load_response(args.input)

        record = analysis.extract_record(payload, args.cve)
        report = analysis.build_report(record, args.cve, VARIANT_NUMBER)
    except api_client.NvdError as error:
        print(error, file=sys.stderr)
        return 1
    except OSError:
        print("Не вдалося прочитати локальний файл.", file=sys.stderr)
        return 1
    except (json.JSONDecodeError, UnicodeDecodeError):
        print("Локальний файл має містити коректний JSON у UTF-8.", file=sys.stderr)
        return 1
    except ValueError as error:
        print(f"Помилка даних: {error}", file=sys.stderr)
        return 1

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
