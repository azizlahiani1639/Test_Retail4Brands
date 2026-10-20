"""Offline checks; these do not use your API key or call Gemini."""

from contextlib import redirect_stderr
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from google.genai.errors import ClientError

from ex2.analyze_image import DailyQuotaError, analyze_image, main


class AnalyzeImageTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.image = Path(self.directory.name) / "product.jpg"
        self.image.write_bytes(b"image bytes")
        self.environment = patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.dotenv = patch("ex2.analyze_image.load_dotenv")
        self.dotenv.start()
        self.addCleanup(self.dotenv.stop)
        self.client_patch = patch("ex2.analyze_image.genai.Client")
        self.client = self.client_patch.start().return_value.__enter__.return_value
        self.addCleanup(self.client_patch.stop)

    def test_reads_image_and_returns_boolean_and_explanation(self):
        for value in (True, False):
            answer = {"has_size_info": value, "explanation": "Visible evidence."}
            self.client.models.generate_content.return_value = Mock(text=json.dumps(answer))
            self.assertEqual(analyze_image(str(self.image)), answer)
        image_part = self.client.models.generate_content.call_args.kwargs["contents"][1]
        self.assertEqual(image_part.inline_data.data, b"image bytes")
        self.assertEqual(image_part.inline_data.mime_type, "image/jpeg")

    def test_uses_the_shared_prompt_file(self):
        self.client.models.generate_content.return_value = Mock(text=json.dumps({
            "has_size_info": False, "explanation": "No dimensions.",
        }))
        with patch("ex2.analyze_image.PROMPT_FILE") as prompt_file:
            prompt_file.read_text.return_value = "Shared prompt from the text file"
            analyze_image(str(self.image))
        contents = self.client.models.generate_content.call_args.kwargs["contents"]
        self.assertEqual(contents[0], "Shared prompt from the text file")

    def test_empty_prompt_fails_before_calling_gemini(self):
        with self.assertRaises(ValueError):
            analyze_image(str(self.image), " ")
        self.client.models.generate_content.assert_not_called()

    @patch("ex2.analyze_image.requests.get")
    def test_downloads_direct_image_url(self, get):
        get.return_value = Mock(content=b"remote image", headers={"Content-Type": "image/png"})
        self.client.models.generate_content.return_value = Mock(text=json.dumps({
            "has_size_info": False, "explanation": "No dimensions.",
        }))
        self.assertIs(analyze_image("https://example.com/image.png")["has_size_info"], False)
        self.assertEqual(get.call_args.kwargs["timeout"], 60)

    @patch.dict("os.environ", {"GEMINI_API_KEY": ""})
    def test_missing_key(self):
        with self.assertRaises(ValueError):
            analyze_image(str(self.image))
        self.client.models.generate_content.assert_not_called()

    def test_missing_or_invalid_answer_is_an_error(self):
        for text in (None, "not JSON", '{"has_size_info": "false", "explanation": "Bad type"}'):
            self.client.models.generate_content.return_value = Mock(text=text)
            with self.subTest(text=text), self.assertRaises(ValueError):
                analyze_image(str(self.image))

    def test_api_failure_produces_cli_error(self):
        self.client.models.generate_content.side_effect = RuntimeError("API unavailable")
        with redirect_stderr(StringIO()) as stderr:
            self.assertEqual(main(["-i", str(self.image)]), 1)
        self.assertIn("API unavailable", stderr.getvalue())

    @patch("ex2.analyze_image.time.sleep")
    def test_rate_limit_retries_the_same_image_after_waiting(self, sleep):
        answer = {"has_size_info": False, "explanation": "No size shown."}
        self.client.models.generate_content.side_effect = [
            ClientError(429, {"error": {"message": "Rate limited"}}),
            Mock(text=json.dumps(answer)),
        ]
        with redirect_stderr(StringIO()):
            self.assertEqual(analyze_image(str(self.image)), answer)
        sleep.assert_called_once_with(60)
        self.assertEqual(self.client.models.generate_content.call_count, 2)

    @patch("ex2.analyze_image.time.sleep")
    def test_rate_limit_retries_are_bounded(self, sleep):
        self.client.models.generate_content.side_effect = ClientError(429, {"error": {"message": "Quota exhausted"}})
        with redirect_stderr(StringIO()), self.assertRaisesRegex(ValueError, "after 3 attempts"):
            analyze_image(str(self.image))
        self.assertEqual(self.client.models.generate_content.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    @patch("ex2.analyze_image.time.sleep")
    def test_invalid_key_is_not_retried(self, sleep):
        self.client.models.generate_content.side_effect = ClientError(403, {"error": {"message": "Denied"}})
        with self.assertRaises(ClientError):
            analyze_image(str(self.image))
        sleep.assert_not_called()

    @patch("ex2.analyze_image.time.sleep")
    def test_daily_quota_stops_without_waiting_or_retrying(self, sleep):
        self.client.models.generate_content.side_effect = ClientError(429, {"error": {
            "message": "Daily quota exceeded",
            "details": [{"violations": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier"}]}],
        }})
        with self.assertRaises(DailyQuotaError):
            analyze_image(str(self.image))
        self.assertEqual(self.client.models.generate_content.call_count, 1)
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
