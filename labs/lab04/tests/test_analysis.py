from copy import deepcopy

import pytest

from labs.lab04.analysis import build_report, extract_record

CVE_ID = "CVE-2099-10001"


def report_for(payload: dict) -> dict:
    record = extract_record(payload, CVE_ID)
    return build_report(record, CVE_ID, 13)


@pytest.mark.parametrize(
    ("score", "impact", "expected"),
    [
        (5.9, "LOW", "other"),
        (6.0, "LOW", "review"),
        (6.1, "LOW", "review"),
        (9.8, "HIGH", "other"),
    ],
)
def test_rule(payload: dict, score: float, impact: str, expected: str) -> None:
    cve = payload["vulnerabilities"][0]["cve"]
    data = cve["metrics"]["cvssMetricV31"][0]["cvssData"]
    data.update(baseScore=score, integrityImpact=impact)

    assert report_for(payload)["decision"] == expected


def test_not_found() -> None:
    assert report_for({"vulnerabilities": []})["decision"] == "not_found"


def test_rejected(payload: dict) -> None:
    payload["vulnerabilities"][0]["cve"]["vulnStatus"] = "Rejected"
    assert report_for(payload)["decision"] == "rejected"


@pytest.mark.parametrize("missing", ["metrics", "integrityImpact"])
def test_insufficient_data(payload: dict, missing: str) -> None:
    cve = payload["vulnerabilities"][0]["cve"]
    if missing == "metrics":
        del cve["metrics"]
    else:
        del cve["metrics"]["cvssMetricV31"][0]["cvssData"]["integrityImpact"]

    assert report_for(payload)["decision"] == "insufficient_data"


def test_invalid_impact(payload: dict) -> None:
    cve = payload["vulnerabilities"][0]["cve"]
    data = cve["metrics"]["cvssMetricV31"][0]["cvssData"]
    data["integrityImpact"] = "UNKNOWN"

    with pytest.raises(ValueError, match="integrityImpact"):
        report_for(payload)


@pytest.mark.parametrize(
    ("second_type", "expected_source"),
    [("Primary", "nvd@nist.gov"), ("Secondary", "secondary@example.com")],
)
def test_metric_selection(
    payload: dict, second_type: str, expected_source: str
) -> None:
    entries = payload["vulnerabilities"][0]["cve"]["metrics"]["cvssMetricV31"]
    entries[0]["type"] = second_type
    first = deepcopy(entries[0])
    first.update(type="Secondary", source="secondary@example.com")
    entries.insert(0, first)
    entries.append({**entries[1], "source": "third@example.com"})

    assert report_for(payload)["score_source"] == expected_source