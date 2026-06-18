"""Tests for src/parser.py — Qualtrics CSV parsing."""

import pytest
from src.parser import parse_csv, _is_importid_row, METADATA_COLUMNS

# Qualtrics 3-row header CSV with known properties:
# - 4 respondents
# - R_003 is incomplete (Progress=75)
# - R_002 is a straight-liner on Q2
# - R_003 has missing values on Q2_1 and Q2_3
# - R_001 and R_004 share IP 192.168.1.1
QUALTRICS_CSV = """ResponseId,Status,IPAddress,Progress,Duration (in seconds),Finished,Q1,Q2_1,Q2_2,Q2_3
Response ID,Response Type,IP Address,Progress,Duration (in seconds),Finished,Rate stress (1-7),Mood 1,Mood 2,Mood 3
{"ImportId":"responseId"},{"ImportId":"status"},{"ImportId":"ipAddress"},{"ImportId":"progress"},{"ImportId":"duration"},{"ImportId":"finished"},{"ImportId":"QID1"},{"ImportId":"QID2_1"},{"ImportId":"QID2_2"},{"ImportId":"QID2_3"}
R_001,IP Address,192.168.1.1,100,180,True,4,3,4,3
R_002,IP Address,192.168.1.2,100,45,True,5,5,5,5
R_003,IP Address,192.168.1.3,75,120,False,3,,2,
R_004,IP Address,192.168.1.1,100,200,True,2,4,3,5
"""

STANDARD_CSV = """name,age,score
Alice,30,85
Bob,25,90
Carol,,72
"""

QUALTRICS_NO_IMPORTID = """ResponseId,Progress,Q1
Response ID,Progress,My question
R_001,100,3
R_002,100,4
"""


class TestImportIdDetection:
    def test_detects_importid_row(self):
        row = ['{"ImportId":"responseId"}', '{"ImportId":"QID1"}']
        assert _is_importid_row(row) is True

    def test_rejects_plain_row(self):
        row = ["R_001", "100", "4"]
        assert _is_importid_row(row) is False

    def test_partial_importid_row(self):
        row = ["plain text", '{"ImportId":"QID1"}', "other"]
        assert _is_importid_row(row) is True


class TestQualtricsFormatParsing:
    def setup_method(self):
        self.survey = parse_csv(QUALTRICS_CSV)

    def test_detects_qualtrics_format(self):
        assert self.survey.is_qualtrics_format is True

    def test_column_names_from_row0(self):
        assert self.survey.columns[0].name == "ResponseId"
        assert self.survey.columns[4].name == "Duration (in seconds)"

    def test_question_text_from_row1(self):
        # Q1 question text comes from row 1
        q1_col = next(c for c in self.survey.columns if c.name == "Q1")
        assert q1_col.question_text == "Rate stress (1-7)"

    def test_import_id_parsed(self):
        resp_col = self.survey.columns[0]
        assert resp_col.import_id == '{"ImportId":"responseId"}'

    def test_respondent_count(self):
        assert self.survey.respondent_count == 4

    def test_data_starts_after_importid_row(self):
        # First data row should be R_001, not an ImportId row
        first_row = self.survey.rows[0]
        assert first_row["ResponseId"] == "R_001"

    def test_missing_values_become_none(self):
        # R_003 has empty Q2_1 and Q2_3
        r003 = next(r for r in self.survey.rows if r["ResponseId"] == "R_003")
        assert r003["Q2_1"] is None
        assert r003["Q2_3"] is None

    def test_non_missing_values_preserved(self):
        r001 = next(r for r in self.survey.rows if r["ResponseId"] == "R_001")
        assert r001["Q2_1"] == "3"
        assert r001["Q1"] == "4"


class TestStandardCSVParsing:
    def setup_method(self):
        self.survey = parse_csv(STANDARD_CSV)

    def test_not_detected_as_qualtrics(self):
        assert self.survey.is_qualtrics_format is False

    def test_column_names_from_header_row(self):
        assert self.survey.columns[0].name == "name"
        assert self.survey.columns[1].name == "age"

    def test_respondent_count(self):
        assert self.survey.respondent_count == 3

    def test_missing_age_is_none(self):
        carol = self.survey.rows[2]
        assert carol["age"] is None

    def test_question_text_equals_name_for_standard_csv(self):
        assert self.survey.columns[0].question_text == "name"


class TestEdgeCases:
    def test_raises_on_empty_content(self):
        with pytest.raises(ValueError):
            parse_csv("")

    def test_raises_on_whitespace_only(self):
        with pytest.raises(ValueError):
            parse_csv("   \n   ")

    def test_question_column_names_excludes_metadata(self):
        survey = parse_csv(QUALTRICS_CSV)
        q_cols = survey.question_column_names
        assert "ResponseId" not in q_cols
        assert "Progress" not in q_cols
        assert "IPAddress" not in q_cols
        assert "Q1" in q_cols
        assert "Q2_1" in q_cols
