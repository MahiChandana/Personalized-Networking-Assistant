import httpx
from urllib.parse import quote


class FactChecker:
    SEARCH_URL = "https://en.wikipedia.org/w/api.php"
    SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{}"

    def __init__(self):
        self.headers = {
            "User-Agent": "PersonalizedNetworkingAssistant/1.0 (Student Project; contact@example.com)"
        }

    def verify_topic(self, query: str):
        try:
            # Search page
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json"
            }

            response = httpx.get(
                self.SEARCH_URL,
                params=params,
                headers=self.headers,
                timeout=20
            )

            response.raise_for_status()

            data = response.json()

            results = data["query"]["search"]

            if len(results) == 0:
                return {
                    "status": "Not Found",
                    "title": "",
                    "summary": "No matching topic found.",
                    "url": ""
                }

            title = results[0]["title"]

            summary = httpx.get(
                self.SUMMARY_URL.format(quote(title)),
                headers=self.headers,
                timeout=20
            )

            summary.raise_for_status()

            page = summary.json()

            return {
                "status": "Verified",
                "title": page.get("title", title),
                "summary": page.get("extract", ""),
                "url": page.get("content_urls", {})
                          .get("desktop", {})
                          .get("page", "")
            }

        except Exception as e:
            return {
                "status": "Error",
                "title": query,
                "summary": str(e),
                "url": ""
            }