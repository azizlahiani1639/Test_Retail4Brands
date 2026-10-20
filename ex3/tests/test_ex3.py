"""Offline checks for the boolean function and prompt evaluation rules."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from ex3.check_size import has_size_info, main
from ex3.test_suite_prompt import test_prompt
from ex2.analyze_image import DailyQuotaError


class BooleanTests(unittest.TestCase):
    @patch("ex3.check_size.analyze_image")
    def test_returns_boolean(self, analyze):
        for expected in (True, False):
            analyze.return_value = {"has_size_info": expected, "explanation": "Evidence."}
            self.assertIs(has_size_info("https://example.com/image.jpg"), expected)
        analyze.assert_called_with("https://example.com/image.jpg", None)

    @patch("ex3.check_size.analyze_image")
    def test_passes_custom_prompt_to_analysis(self, analyze):
        analyze.return_value = {"has_size_info": True, "explanation": "12 cm."}
        self.assertIs(has_size_info("image.jpg", "My test prompt"), True)
        analyze.assert_called_once_with("image.jpg", "My test prompt")

    @patch("ex3.check_size.analyze_image", side_effect=ValueError("API failed"))
    def test_api_error_is_not_a_false_answer(self, analyze):
        with self.assertRaises(ValueError):
            has_size_info("https://example.com/image.jpg")

    @patch("ex3.check_size.has_size_info", return_value=False)
    def test_cli_analyzes_image_url(self, analyze):
        with redirect_stdout(StringIO()) as stdout:
            self.assertEqual(main(["-i", "https://example.com/image.jpg"]), 0)
        self.assertEqual(stdout.getvalue(), "false\n")
        analyze.assert_called_once_with("https://example.com/image.jpg")

    @patch("ex3.check_size.has_size_info")
    def test_cli_rejects_asin_and_local_path(self, analyze):
        for source in ("B07N7WT6J8", "image.jpg"):
            with self.subTest(source=source), redirect_stderr(StringIO()):
                with self.assertRaises(SystemExit) as error:
                    main(["-i", source])
                self.assertEqual(error.exception.code, 2)
        analyze.assert_not_called()


class PromptRunnerTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.suite = Path(self.directory.name)
        (self.suite / "prompt.txt").write_text("My evaluation prompt")
        for folder in ("with_size", "without"):
            directory = self.suite / "test_images" / folder
            directory.mkdir(parents=True)
            (directory / "example.jpg").write_bytes(b"image")
        directory_patch = patch.object(test_prompt, "SUITE_DIR", self.suite)
        directory_patch.start()
        self.addCleanup(directory_patch.stop)

    @patch("ex3.test_suite_prompt.test_prompt.has_size_info", side_effect=[True, False])
    def test_all_correct_pass_and_use_file_prompt(self, analyze):
        with redirect_stdout(StringIO()) as stdout:
            self.assertEqual(test_prompt.main(), 0)
        self.assertIn("2/2 (100.0%)", stdout.getvalue())
        self.assertTrue(all(call.args[1] == "My evaluation prompt" for call in analyze.call_args_list))

    @patch("ex3.test_suite_prompt.test_prompt.has_size_info", side_effect=[False, False])
    def test_wrong_prediction_fails(self, analyze):
        with redirect_stdout(StringIO()) as stdout:
            self.assertEqual(test_prompt.main(), 1)
        self.assertIn("1/2 (50.0%)", stdout.getvalue())

    @patch("ex3.test_suite_prompt.test_prompt.has_size_info", side_effect=[RuntimeError("quota"), False])
    def test_api_error_still_tests_other_images_and_fails(self, analyze):
        with redirect_stdout(StringIO()) as stdout:
            self.assertEqual(test_prompt.main(), 1)
        self.assertEqual(analyze.call_count, 2)
        self.assertIn("API/file errors: 1", stdout.getvalue())
        self.assertIn("Completed: 1/2", stdout.getvalue())
        self.assertIn("Prediction accuracy: 1/1 (100.0%)", stdout.getvalue())
        self.assertIn("Target 100%: INCOMPLETE", stdout.getvalue())

    @patch("ex3.test_suite_prompt.test_prompt.has_size_info", side_effect=RuntimeError("offline"))
    def test_no_completed_predictions_has_no_accuracy_percentage(self, analyze):
        with redirect_stdout(StringIO()) as stdout:
            self.assertEqual(test_prompt.main(), 1)
        self.assertIn("Completed: 0/2", stdout.getvalue())
        self.assertIn("Prediction accuracy: unavailable", stdout.getvalue())

    @patch("ex3.test_suite_prompt.test_prompt.has_size_info", side_effect=DailyQuotaError("Daily quota exhausted"))
    def test_daily_quota_stops_suite_and_reports_untested_images(self, analyze):
        with redirect_stdout(StringIO()) as stdout:
            self.assertEqual(test_prompt.main(), 1)
        self.assertEqual(analyze.call_count, 1)
        self.assertIn("STOP", stdout.getvalue())
        self.assertIn("Completed: 0/2", stdout.getvalue())
        self.assertIn("Not tested: 1", stdout.getvalue())
        self.assertIn("INCOMPLETE", stdout.getvalue())

    @patch("ex3.test_suite_prompt.test_prompt.has_size_info")
    def test_empty_class_fails_before_any_api_requests(self, analyze):
        (self.suite / "test_images" / "without" / "example.jpg").unlink()
        with redirect_stderr(StringIO()):
            self.assertEqual(test_prompt.main(), 2)
        analyze.assert_not_called()

    @patch("ex3.test_suite_prompt.test_prompt.has_size_info")
    def test_empty_prompt_fails_before_any_api_requests(self, analyze):
        (self.suite / "prompt.txt").write_text(" ")
        with redirect_stderr(StringIO()):
            self.assertEqual(test_prompt.main(), 2)
        analyze.assert_not_called()


if __name__ == "__main__":
    unittest.main()
