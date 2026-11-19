import os

import requests

NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"


class NvdError(Exception):
    """Помилка отримання даних від NVD."""


def build_headers() -> dict[str, str]:
    """Зібрати HTTP-заголовки для запиту до NVD."""
    headers = {"Accept": "application/json"}
    key = os.getenv("NVD_API_KEY", "").strip()
    if key:
        headers["apiKey"] = key
    return headers


def fetch_response(cve_id: str) -> object:
    """Отримати й декодувати відповідь NVD для одного CVE."""
    try:
        response = requests.get(
            NVD_URL,
            params={"cveId": cve_id},
            headers=build_headers(),
            timeout=(3.05, 10),
            allow_redirects=False,
        )
        response.raise_for_status()
        if response.status_code != 200:
            raise NvdError(f"Неочікуваний статус NVD: HTTP {response.status_code}.")
        return response.json()
    except requests.exceptions.HTTPError as error:
        if error.response is None:
            raise NvdError("HTTP-помилка NVD.") from None
        raise NvdError(f"Помилка NVD: HTTP {error.response.status_code}.") from None
    except requests.exceptions.Timeout:
        raise NvdError("Перевищено час очікування відповіді NVD.") from None
    except requests.exceptions.JSONDecodeError:
        raise NvdError("NVD повернула некоректний JSON.") from None
    except requests.exceptions.RequestException:
        raise NvdError("Не вдалося виконати запит до NVD.") from None