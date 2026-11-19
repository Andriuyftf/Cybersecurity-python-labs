import json
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NVD_API_KEY", raising=False)
    monkeypatch.delattr("requests.sessions.Session.request")


@pytest.fixture
def payload() -> dict:
    path = Path(__file__).resolve().parents[1] / "data" / "nvd_sample.json"
    return json.loads(path.read_text(encoding="utf-8"))