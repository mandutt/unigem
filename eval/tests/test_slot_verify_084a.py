"""Tests for D-084 rev3 / 084a URL-only verifier."""
from __future__ import annotations

import unittest

from eval.slot_verify_084a import VERIFIER_VERSION, verify_084a


class TestUrlBoundary(unittest.TestCase):
    def test_hangul_particle_not_in_url(self) -> None:
        r = verify_084a(
            "문의는 https://coronamap.site에서 확인",
            "문의는 https://coronamap.site에서 확인",
        )
        self.assertEqual(r.source_urls[0].raw, "https://coronamap.site")
        self.assertEqual(r.summary_urls[0].raw, "https://coronamap.site")
        self.assertTrue(r.grounded)

    def test_corona_wrap_source_and_summary(self) -> None:
        source = "링크 http://coronamap.\n site 를 확인"
        summary = "링크 http://coronamap.site 를 확인"
        r = verify_084a(source, summary)
        self.assertTrue(r.grounded)
        self.assertTrue(any("coronamap.site" in x.joined for x in r.url_repairs))

    def test_summary_wrap_is_source_attested(self) -> None:
        source = "링크 http://coronamap.site 를 확인"
        summary = "링크 http://coronamap.\n site 를 확인"
        r = verify_084a(source, summary)
        self.assertTrue(r.grounded)
        self.assertTrue(any(x.reason == "summary_source_match" for x in r.url_repairs))

    def test_summary_wrap_without_source_is_unresolved(self) -> None:
        source = "링크 http://other.example 를 확인"
        summary = "링크 http://coronamap.\n site 를 확인"
        r = verify_084a(source, summary)
        self.assertFalse(r.grounded)
        self.assertTrue(any(x.reason == "summary_wrap_not_in_source" for x in r.unresolved))

    def test_fine_fss_ambiguous_host_is_unresolved(self) -> None:
        source = "기사 http://fine.fss.\n or.kr 를 확인"
        r = verify_084a(source, source)
        self.assertTrue(any(x.reason == "ambiguous_host_wrap" for x in r.unresolved))

    def test_trailing_punctuation_is_unresolved(self) -> None:
        r = verify_084a("참고 http://example.com.", "참고 http://example.com.")
        self.assertTrue(any(x.reason == "terminal_punctuation" for x in r.unresolved))
        self.assertFalse(r.grounded)

    def test_blank_line_does_not_join(self) -> None:
        source = "http://coronamap.\n\n site"
        r = verify_084a(source, source)
        self.assertFalse(r.url_repairs)

    def test_strict_url_case_and_comma(self) -> None:
        source = "https://example.com/Case?key=A,B"
        summary = "https://example.com/case?key=ab"
        r = verify_084a(source, summary)
        self.assertFalse(r.grounded)
        self.assertTrue(r.new)

    def test_trailing_slash_preserved(self) -> None:
        r = verify_084a("https://example.com/", "https://example.com")
        self.assertFalse(r.grounded)
        self.assertTrue(r.new)


class TestNonUrlSlots(unittest.TestCase):
    def test_non_url_slot_preserved(self) -> None:
        source = "회의는 18일 열렸다"
        summary = "회의는 18일 열렸다"
        r = verify_084a(source, summary)
        self.assertTrue(r.grounded)
        self.assertFalse(r.new)
        self.assertFalse(r.missing)

    def test_url_digits_not_double_extracted(self) -> None:
        source = "링크 https://example.com/2020/01"
        summary = "링크 https://example.com/2020/01"
        r = verify_084a(source, summary)
        self.assertTrue(r.grounded)
        self.assertEqual({s.kind for s in r.source_slots}, {"url"})

    def test_version_is_set(self) -> None:
        r = verify_084a("a", "a")
        self.assertEqual(r.verifier_version, VERIFIER_VERSION)


if __name__ == "__main__":
    unittest.main()
