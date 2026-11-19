import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from labs.lab04 import main as cli

CVE_ID = "CVE-2099-10001"


def test_local_report(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    payload: dict,
) -> None:
    path = tmp_path / "sample.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    fetch = Mock()
    monkeypatch.setattr(cli.api_client, "fetch_response", fetch)

    assert cli.main(["--cve", CVE_ID, "--input", str(path)]) == 0
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert report["cve_id"] == CVE_ID
    assert report["variant"] == 13
    assert report["decision"] == "other"
    assert captured.err == ""
    fetch.assert_not_called()


def test_invalid_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{", encoding="utf-8")

    assert cli.main(["--cve", CVE_ID, "--input", str(path)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "JSON" in captured.err