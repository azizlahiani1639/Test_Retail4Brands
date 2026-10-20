"""Small offline tests for extraction, downloading, and the command line."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

import requests

from ex1.extract_image import DEFAULT_OUTPUT, download_image, get_main_image_url, main


class ExtractImageTests(unittest.TestCase):
    @patch("ex1.extract_image.requests.get")
    def test_main_image_url(self, get):
        get.return_value = Mock(text='''<img src="https://example.com/logo.jpg">
            <img id="landingImage" src="https://example.com/small.jpg"
                 data-old-hires="https://example.com/main.jpg">''')
        self.assertEqual(get_main_image_url("b07n7wt6j8"), "https://example.com/main.jpg")
        self.assertEqual(get.call_args.args[0], "https://www.amazon.fr/dp/B07N7WT6J8")

    @patch("ex1.extract_image.requests.get")
    def test_displayed_image_and_book_cover_fallback(self, get):
        for image_id in ("landingImage", "imgBlkFront", "ebooksImgBlkFront"):
            get.return_value = Mock(text=f'<img id="{image_id}" src="https://example.com/main.jpg">')
            with self.subTest(image_id=image_id):
                self.assertEqual(get_main_image_url("B07N7WT6J8"), "https://example.com/main.jpg")

    @patch("ex1.extract_image.requests.get")
    def test_invalid_asin_never_makes_a_request(self, get):
        with self.assertRaises(ValueError):
            get_main_image_url("not-an-asin")
        get.assert_not_called()

    @patch("ex1.extract_image.requests.get")
    def test_captcha_and_missing_image(self, get):
        for html in ('<form action="/errors/validateCaptcha"></form>',
                     '<img src="https://example.com/logo.jpg">',
                     '<img id="landingImage" src="data:image/gif;base64,AAAA">'):
            get.return_value = Mock(text=html)
            with self.subTest(html=html), self.assertRaises(ValueError):
                get_main_image_url("B07N7WT6J8")

    @patch("ex1.extract_image.requests.get")
    def test_download_saves_image_in_requested_folder(self, get):
        get.return_value = Mock(headers={"Content-Type": "image/png"}, content=b"image bytes")
        with TemporaryDirectory() as directory:
            output = Path(directory) / "images"
            path = download_image("https://example.com/main.png", "B07N7WT6J8", output)
            self.assertEqual(path.name, "B07N7WT6J8.png")
            self.assertEqual(path.parent, output.resolve())
            self.assertEqual(path.read_bytes(), b"image bytes")

    @patch("ex1.extract_image.requests.get")
    def test_html_or_empty_response_is_not_saved(self, get):
        for content_type, content in (("text/html", b"blocked"), ("image/jpeg", b"")):
            get.return_value = Mock(headers={"Content-Type": content_type}, content=content)
            with TemporaryDirectory() as directory:
                output = Path(directory) / "images"
                with self.assertRaises(ValueError):
                    download_image("https://example.com/main.jpg", "B07N7WT6J8", output)
                self.assertFalse(output.exists())

    @patch("ex1.extract_image.requests.get")
    def test_cli_fetches_then_downloads(self, get):
        get.side_effect = [
            Mock(text='<img id="landingImage" src="https://example.com/main.jpg">'),
            Mock(headers={"Content-Type": "image/jpeg"}, content=b"image bytes"),
        ]
        with TemporaryDirectory() as directory, redirect_stdout(StringIO()) as stdout:
            self.assertEqual(main(["-i", "b07n7wt6j8", "-o", directory]), 0)
            self.assertEqual((Path(directory) / "B07N7WT6J8.jpg").read_bytes(), b"image bytes")
            self.assertIn("Saved to:", stdout.getvalue())
        self.assertEqual(DEFAULT_OUTPUT, Path(__file__).resolve().parents[1] / "test_images")

    @patch("ex1.extract_image.requests.get", side_effect=requests.Timeout("Timed out"))
    def test_cli_reports_network_error(self, get):
        with redirect_stderr(StringIO()) as stderr:
            self.assertEqual(main(["-i", "B07N7WT6J8"]), 1)
        self.assertIn("Timed out", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
