from unittest.mock import Mock

import pytest
import requests

from labs.lab04 import api_client

CVE_ID = "CVE-2099-10001"


@pytest.mark.parametrize("key", [None, "fake-key"])
def test_fetch_response(monkeypatch: pytest.MonkeyPatch, key: str | None) -> None:
    headers = {"Accept": "application/json"}
    if key is not None:
        monkeypatch.setenv("NVD_API_KEY", key)
        headers["apiKey"] = key

    payload = {"vulnerabilities": []}
    response = Mock(spec=requests.Response, status_code=200)
    response.json.return_value = payload
    fake_get = Mock(return_value=response)
    monkeypatch.setattr(api_client.requests, "get", fake_get)

    assert api_client.fetch_response(CVE_ID) == payload
    fake_get.assert_called_once_with(
        "https://services.nvd.nist.gov/rest/json/cves/2.0",
        params={"cveId": CVE_ID},
        headers=headers,
        timeout=(3.05, 10),
        allow_redirects=False,
    )


def test_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    response = Mock(spec=requests.Response, status_code=404)
    response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        response=response
    )
    monkeypatch.setattr(api_client.requests, "get", Mock(return_value=response))

    with pytest.raises(api_client.NvdError, match="404"):
        api_client.fetch_response(CVE_ID)