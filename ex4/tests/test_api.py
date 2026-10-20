"""Exercise the HTTP endpoint without calling Amazon or Gemini."""

import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient
from google.genai.errors import ClientError
import requests

from ex2.analyze_image import DailyQuotaError
from ex4.app import app

client = TestClient(app)


class ApiTests(unittest.TestCase):
    @patch("ex4.app.has_size_info")
    @patch("ex4.app.get_main_image_url", return_value="https://example.com/main.jpg")
    def test_returns_asin_image_and_real_boolean(self, extract, analyze):
        for expected in (True, False):
            analyze.return_value = expected
            response = client.get("/analyze/b07n7wt6j8")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {
                "asin": "B07N7WT6J8",
                "image_url": "https://example.com/main.jpg",
                "has_size_info": expected,
            })
        extract.assert_called_with("B07N7WT6J8")
        analyze.assert_called_with("https://example.com/main.jpg")

    @patch("ex4.app.get_main_image_url")
    def test_invalid_asin_fails_before_external_calls(self, extract):
        for asin in ("bad", "A" * 11, "B07N7WT6J!"):
            with self.subTest(asin=asin):
                response = client.get(f"/analyze/{asin}")
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json()["detail"][0]["loc"], ["path", "asin"])
        extract.assert_not_called()

    @patch("ex4.app.has_size_info")
    @patch("ex4.app.get_main_image_url", side_effect=ValueError("Main image not found"))
    def test_missing_image_is_an_error(self, extract, analyze):
        response = client.get("/analyze/B07N7WT6J8")
        self.assertEqual(response.status_code, 502)
        self.assertIn("Main image not found", response.json()["detail"])
        analyze.assert_not_called()

    @patch("ex4.app.get_main_image_url", side_effect=requests.Timeout)
    def test_timeout_returns_504(self, extract):
        self.assertEqual(client.get("/analyze/B07N7WT6J8").status_code, 504)

    @patch("ex4.app.has_size_info", side_effect=httpx.ReadTimeout("Gemini timed out"))
    @patch("ex4.app.get_main_image_url", return_value="https://example.com/main.jpg")
    def test_gemini_transport_timeout_returns_504(self, extract, analyze):
        self.assertEqual(client.get("/analyze/B07N7WT6J8").status_code, 504)

    @patch("ex4.app.has_size_info", side_effect=DailyQuotaError("Daily quota exhausted"))
    @patch("ex4.app.get_main_image_url", return_value="https://example.com/main.jpg")
    def test_daily_quota_returns_503(self, extract, analyze):
        response = client.get("/analyze/B07N7WT6J8")
        self.assertEqual(response.status_code, 503)
        self.assertIn("Daily quota exhausted", response.json()["detail"])

    @patch("ex4.app.has_size_info", side_effect=ClientError(403, {"error": {"message": "Denied"}}))
    @patch("ex4.app.get_main_image_url", return_value="https://example.com/main.jpg")
    def test_gemini_error_returns_502(self, extract, analyze):
        self.assertEqual(client.get("/analyze/B07N7WT6J8").status_code, 502)

    def test_documentation_exposes_boolean_response(self):
        schema = client.get("/openapi.json").json()
        properties = schema["components"]["schemas"]["ProductAnalysis"]["properties"]
        self.assertEqual(properties["has_size_info"]["type"], "boolean")
        self.assertEqual(client.get("/docs").status_code, 200)


if __name__ == "__main__":
    unittest.main()
