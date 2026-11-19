VARIANT = 13


class DataError(ValueError):
    """Дані відповіді не відповідають вимогам лабораторної."""


def _optional_text(data: dict, key: str) -> str | None:
    if key not in data:
        return None
    value = data[key]
    if not isinstance(value, str) or not value.strip():
        raise DataError(f"{key} має бути непорожнім рядком.")
    return value


def _english_description(cve: dict) -> str | None:
    descriptions = cve.get("descriptions", [])
    if not isinstance(descriptions, list):
        raise DataError("descriptions має бути списком.")

    description = None
    for item in descriptions:
        if not isinstance(item, dict):
            raise DataError("Елемент descriptions має бути об'єктом.")
        lang, value = item.get("lang"), item.get("value")
        if not isinstance(lang, str) or not isinstance(value, str):
            raise DataError("lang і value мають бути рядками.")
        if description is None and lang == "en" and value.strip():
            description = value

    return description


def _select_metric(cve: dict) -> dict | None:
    metrics = cve.get("metrics", {})
    if not isinstance(metrics, dict):
        raise DataError("metrics має бути об'єктом.")

    entries = metrics.get("cvssMetricV31", [])
    if not isinstance(entries, list):
        raise DataError("cvssMetricV31 має бути списком.")
    if any(not isinstance(entry, dict) for entry in entries):
        raise DataError("Елементи cvssMetricV31 мають бути об'єктами.")

    if not entries:
        return None
    for entry in entries:
        if entry.get("type") == "Primary":
            return entry
    return entries[0]

def extract_record(payload: object, cve_id: str) -> dict | None:
    """Повернути fields для звіту й cvss_data вибраної оцінки або None."""
    if not isinstance(payload, dict):
        raise DataError("Відповідь NVD має бути об'єктом.")

    entries = payload.get("vulnerabilities")
    if not isinstance(entries, list) or len(entries) > 1:
        raise DataError("vulnerabilities має містити нуль або один запис.")
    if not entries:
        return None

    entry = entries[0]
    cve = entry.get("cve") if isinstance(entry, dict) else None
    if not isinstance(cve, dict) or cve.get("id") != cve_id:
        raise DataError("Запис cve відсутній або його id не збігається з --cve.")

    status = _optional_text(cve, "vulnStatus")
    fields = {"description": _english_description(cve), "vuln_status": status}
    record = {"fields": fields, "cvss_data": {}}
    if status is None or status == "Rejected":
        return record

    metric = _select_metric(cve)
    if metric is None:
        return record

    data = metric.get("cvssData")
    if not isinstance(data, dict):
        raise DataError("cvssData має бути об'єктом.")

    score = data.get("baseScore")
    if type(score) not in (int, float) or not 0 <= score <= 10:
        raise DataError("baseScore має бути числом від 0 до 10.")
    version = _optional_text(data, "version")
    if version is not None and version != "3.1":
        raise DataError('Поле version має дорівнювати "3.1".')

    fields.update(
        cvss_version=version,
        score=score,
        score_source=_optional_text(metric, "source"),
        vector=_optional_text(data, "vectorString"),
    )
    record["cvss_data"] = data.copy()
    return record

def build_report(record: dict | None, cve_id: str, variant: int) -> dict:
    """Застосувати правило варіанта 13 і сформувати JSON-сумісний звіт."""
    if type(variant) is not int or variant != VARIANT:
        raise DataError(f"Для цієї роботи потрібен варіант {VARIANT}.")

    threshold, field, expected = 6.0, "integrityImpact", "LOW"
    report = {
        "cve_id": cve_id,
        "variant": variant,
        "description": None,
        "vuln_status": None,
        "cvss_version": None,
        "score": None,
        "score_source": None,
        "vector": None,
        "rule": {"threshold": threshold, "field": field, "expected": expected},
        "observed": None,
        "decision": "not_found",
    }
    if record is None:
        return report

    report.update(record["fields"])
    data = record["cvss_data"]
    if report["vuln_status"] == "Rejected":
        report["decision"] = "rejected"
    elif report["score"] is None or field not in data:
        report["decision"] = "insufficient_data"
    else:
        observed = data[field]
        if observed not in ("NONE", "LOW", "HIGH"):
            raise DataError(f"Некоректне значення поля {field}.")
        report["observed"] = observed
        report["decision"] = "other"
        if report["score"] >= threshold and observed == expected:
            report["decision"] = "review"

    return report