"""Tests for src/report.py — text report, HTML report, and clean CSV."""

import csv
import io
import pytest
from src.parser import parse_csv
from src.quality import compute_quality
from src.report import generate_text_report, generate_html_report, export_clean_csv

QUALTRICS_CSV = """ResponseId,Status,IPAddress,Progress,Duration (in seconds),Finished,Q1,Q2_1,Q2_2,Q2_3
Response ID,Response Type,IP Address,Progress,Duration (in seconds),Finished,Rate stress (1-7),Mood 1,Mood 2,Mood 3
{"ImportId":"responseId"},{"ImportId":"status"},{"ImportId":"ipAddress"},{"ImportId":"progress"},{"ImportId":"duration"},{"ImportId":"finished"},{"ImportId":"QID1"},{"ImportId":"QID2_1"},{"ImportId":"QID2_2"},{"ImportId":"QID2_3"}
R_001,IP Address,192.168.1.1,100,180,True,4,3,4,3
R_002,IP Address,192.168.1.2,100,45,True,5,5,5,5
R_003,IP Address,192.168.1.3,75,120,False,3,,2,
R_004,IP Address,192.168.1.1,100,200,True,2,4,3,5
"""

XSS_CSV = """ResponseId,<script>alert(1)</script>,Progress
R_001,"</td><img src=x onerror=alert(1)>",100
"""


@pytest.fixture
def survey():
    return parse_csv(QUALTRICS_CSV)


@pytest.fixture
def quality(survey):
    return compute_quality(survey)


class TestHTMLReport:
    def test_has_doctype(self, survey, quality):
        html = generate_html_report(quality, survey)
        assert html.strip().startswith("<!DOCTYPE html>")

    def test_contains_respondent_count(self, survey, quality):
        html = generate_html_report(quality, survey)
        assert "4" in html  # 4 total respondents

    def test_contains_completion_rate(self, survey, quality):
        html = generate_html_report(quality, survey)
        assert "75.0%" in html or "75%" in html

    def test_contains_timing_section(self, survey, quality):
        html = generate_html_report(quality, survey)
        assert "Timing" in html
        assert "200" in html  # max duration is 200s (R_004)

    def test_escapes_xss_in_column_names(self):
        survey = parse_csv(XSS_CSV)
        quality = compute_quality(survey)
        html = generate_html_report(quality, survey, source_name="<evil>")
        assert "<script>" not in html
        assert "onerror" not in html
        assert "&lt;script&gt;" in html or "&lt;evil&gt;" in html

    def test_contains_missing_data_section(self, survey, quality):
        html = generate_html_report(quality, survey)
        assert "Missing Data" in html

    def test_source_name_escaped_in_title(self, survey, quality):
        html = generate_html_report(quality, survey, source_name="my<survey>.csv")
        assert "my<survey>.csv" not in html
        assert "my&lt;survey&gt;.csv" in html


class TestTextReport:
    def test_contains_header(self, survey, quality):
        text = generate_text_report(quality, survey)
        assert "QUALTRICS SURVEY DATA QUALITY REPORT" in text

    def test_contains_respondent_count(self, survey, quality):
        text = generate_text_report(quality, survey)
        assert "4" in text

    def test_contains_timing_section(self, survey, quality):
        text = generate_text_report(quality, survey)
        assert "TIMING" in text

    def test_contains_scale_reliability_section(self, survey, quality):
        text = generate_text_report(quality, survey)
        assert "SCALE RELIABILITY" in text


class TestCleanCSVExport:
    def test_incomplete_respondents_excluded(self, survey, quality):
        csv_str = export_clean_csv(survey, quality, exclude_incomplete=True,
                                   exclude_fast=False, exclude_straight_liners=False)
        reader = list(csv.reader(io.StringIO(csv_str)))
        # R_003 (Progress=75) should be excluded
        row_ids = [r[0] for r in reader[1:]]
        assert "R_003" not in row_ids

    def test_fast_respondents_excluded(self, survey, quality):
        csv_str = export_clean_csv(survey, quality, exclude_incomplete=False,
                                   exclude_fast=True, exclude_straight_liners=False)
        reader = list(csv.reader(io.StringIO(csv_str)))
        row_ids = [r[0] for r in reader[1:]]
        assert "R_002" not in row_ids  # R_002 took 45s < 60s threshold

    def test_qi_flags_column_added(self, survey, quality):
        csv_str = export_clean_csv(survey, quality, exclude_incomplete=False,
                                   exclude_fast=False, exclude_straight_liners=False)
        reader = csv.reader(io.StringIO(csv_str))
        header = next(reader)
        assert "QI_Flags" in header

    def test_clean_row_has_empty_flags(self, survey, quality):
        # R_001 has no quality issues (besides duplicate IP)
        csv_str = export_clean_csv(survey, quality, exclude_incomplete=False,
                                   exclude_fast=False, exclude_straight_liners=False)
        reader = list(csv.reader(io.StringIO(csv_str)))
        header = reader[0]
        flags_idx = header.index("QI_Flags")
        # Find R_001 row
        r001 = next(r for r in reader[1:] if r[0] == "R_001")
        # R_001 has duplicate IP flag
        assert "duplicate_ip" in r001[flags_idx]
