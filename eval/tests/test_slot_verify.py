"""Unit tests for F5 slot extraction and summary verification."""
from __future__ import annotations

import unittest

from eval.slot_verify import extract_slots, verify_summary


class SlotExtractionTests(unittest.TestCase):
    def test_fifty_extraction_cases(self) -> None:
        cases: list[tuple[str, str, str]] = []
        for day in range(1, 11):
            value = f"2026-11-{day:02d}"
            cases.append((f"날짜 {value}", "date", value))
        for hour in range(10):
            value = f"{hour:02d}:30"
            cases.append((f"시간 {value}", "time", value))
        for major in range(1, 11):
            value = f"v{major}.2.3"
            cases.append((f"버전 {value}", "version", value))
        for amount in (100, 200, 300, 400, 500, 600, 700, 800, 900, 1000):
            text = f"금액 {amount:,}억원"
            cases.append((text, "number", f"{amount}억원"))
        cases.extend(
            [
                ("https://example.com/a?x=1", "url", "https://example.com/a?x=1"),
                ("http://example.org/b", "url", "http://example.org/b"),
                (r"C:\temp\a.txt", "path", r"C:\temp\a.txt"),
                ("/var/log/app.log", "path", "/var/log/app.log"),
                ("https://example.com/ko", "url", "https://example.com/ko"),
                ("DeepSeek-V4.1-Flash", "identifier", "DeepSeek-V4.1-Flash"),
                ("GPT4", "identifier", "GPT4"),
                ("A100-80GB", "identifier", "A100-80GB"),
                ("vLLM_0.9", "identifier", "vLLM_0.9"),
                ("model-v2", "identifier", "model-v2"),
            ]
        )
        self.assertEqual(len(cases), 50)
        for text, kind, expected in cases:
            with self.subTest(text=text, kind=kind):
                slots = extract_slots(text)
                expected_canon = expected.lower() if kind in {"path", "identifier"} else expected
                self.assertTrue(
                    any(s.kind == kind and s.canonical == expected_canon for s in slots),
                    f"missing {kind}={expected_canon}; got {[s.to_dict() for s in slots]}",
                )

    def test_number_with_compound_unit(self) -> None:
        slots = extract_slots("매출 4조 8000억원")
        values = [s.value for s in slots if s.kind == "number"]
        self.assertIn("4조", values)
        self.assertIn("8000억원", values)

    def test_url_not_broken_by_number(self) -> None:
        slots = extract_slots("https://example.com/v1.2.3")
        self.assertEqual([s.kind for s in slots], ["url"])


class VerifySummaryTests(unittest.TestCase):
    def test_all_preserved(self) -> None:
        source = "2026-11-06 v1.2.3 1,200억원"
        report = verify_summary(source, source)
        self.assertFalse(report.rejected)
        self.assertEqual(report.missing, ())
        self.assertEqual(report.new, ())
        self.assertEqual(report.slot_preservation, 1.0)

    def test_missing_slot_rejected(self) -> None:
        report = verify_summary("2026-11-06 v1.2.3 1,200억원", "2026-11-06 v1.2.3")
        self.assertTrue(report.rejected)
        self.assertIn("1200억원", report.missing)

    def test_new_slot_rejected(self) -> None:
        report = verify_summary("2026-11-06 v1.2.3", "2026-11-06 v1.2.3 999억원")
        self.assertTrue(report.rejected)
        self.assertIn("999억원", report.new)

    def test_no_slots_accepted(self) -> None:
        report = verify_summary("오늘 날씨가 좋다.", "오늘은 맑다.")
        self.assertFalse(report.rejected)
        self.assertEqual(report.source_count, 0)
        self.assertEqual(report.slot_preservation, 1.0)

    def test_date_format_canonicalized(self) -> None:
        report = verify_summary("2026년 11월 6일", "2026-11-06")
        self.assertFalse(report.rejected)

    def test_duplicate_slots_counted_once(self) -> None:
        source = "1,200억원, 1,200억원"
        report = verify_summary(source, "1,200억원")
        self.assertFalse(report.rejected)
        self.assertEqual(report.source_count, 1)

    def test_path_preserved(self) -> None:
        source = r"로그는 C:\temp\app.log 에 있다."
        summary = r"C:\temp\app.log"
        report = verify_summary(source, summary)
        self.assertFalse(report.rejected)

    def test_fullwidth_number_normalized(self) -> None:
        source = "금액 １，２００억원"
        summary = "1,200억원"
        report = verify_summary(source, summary)
        self.assertFalse(report.rejected)


if __name__ == "__main__":
    unittest.main()
