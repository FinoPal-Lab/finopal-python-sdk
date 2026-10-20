"""Tests for the amount helpers, callback parser and error catalogue."""

from __future__ import annotations

import pytest

from finopal import Currency, describe, is_success_status, parse_callback, to_rial, to_toman


class TestToRial:
    @pytest.mark.parametrize(
        "amount,currency,expected",
        [
            (1_100, "IRR", 1_100),
            (1_100, "irr", 1_100),
            (12_000, "IRT", 120_000),
            (12_000, "TOMAN", 120_000),
            (12_000, "toman", 120_000),
            (5, "IRHR", 5_000),
            (5, "IRHT", 50_000),
            (1_100, "UNKNOWN", 1_100),  # unknown falls back to Rial
        ],
    )
    def test_conversions(self, amount, currency, expected):
        assert to_rial(amount, currency) == expected

    def test_accepts_the_enum(self):
        assert to_rial(12_000, Currency.TOMAN) == 120_000

    def test_accepts_numeric_strings(self):
        assert to_rial("1100") == 1100

    def test_rounds_floats(self):
        assert to_rial(1_100.4) == 1100
        assert to_rial(1_100.6) == 1101

    def test_rejects_non_numeric(self):
        with pytest.raises(ValueError, match="must be numeric"):
            to_rial("abc")


class TestToToman:
    def test_divides_by_ten(self):
        assert to_toman(120_000) == 12_000.0

    def test_rejects_non_numeric(self):
        with pytest.raises(ValueError):
            to_toman("abc")


class TestIsSuccessStatus:
    @pytest.mark.parametrize("value", ["OK", "ok", "Ok", "0", " 0 ", 0])
    def test_success_values(self, value):
        assert is_success_status(value) is True

    @pytest.mark.parametrize(
        "value", ["NOK", "nok", "-1", "-138", "", None, "1", "false"]
    )
    def test_failure_values(self, value):
        assert is_success_status(value) is False


class TestParseCallback:
    def test_production_success(self):
        result = parse_callback({"Authority": "FP_ABC", "Status": "OK"})
        assert result.authority == "FP_ABC"
        assert result.status == "OK"
        assert result.is_success is True
        assert result.sandbox is False

    def test_production_failure(self):
        result = parse_callback({"Authority": "FP_ABC", "Status": "NOK"})
        assert result.is_success is False

    def test_sandbox_success(self):
        result = parse_callback(
            {"authority": "FP_ABC", "status": "0", "sandbox": "1", "token": "t"}
        )
        assert result.authority == "FP_ABC"
        assert result.is_success is True
        assert result.sandbox is True

    def test_sandbox_cancelled(self):
        result = parse_callback({"authority": "FP_ABC", "status": "-138"})
        assert result.is_success is False
        assert result.is_cancelled is True

    def test_token_is_used_when_authority_is_missing(self):
        assert parse_callback({"Token": "FP_TOKEN"}).authority == "FP_TOKEN"

    def test_dict_and_attribute_access(self):
        result = parse_callback({"Authority": "FP_ABC", "Status": "OK"})
        assert result["authority"] == "FP_ABC"
        assert result.authority == "FP_ABC"

    def test_unknown_attribute_raises(self):
        with pytest.raises(AttributeError):
            _ = parse_callback({"Authority": "FP_ABC"}).nope

    def test_handles_none(self):
        assert parse_callback(None).is_success is False

    def test_keeps_the_raw_query(self):
        query = {"Authority": "FP_ABC", "Status": "OK"}
        assert parse_callback(query).raw == query


class TestErrorCatalogue:
    @pytest.mark.parametrize(
        "code,needle",
        [
            (-9, "Validation error"),
            (-11, "not active"),
            (-14, "callback URL domain"),
            (100, "Success"),
            (101, "already verified"),
            (-41, "100,000,000"),
            (-50, "paid amount differs"),
            (-54, "Invalid authority"),
            (-1551, "already been reversed"),
            (-1552, "15-minute"),
        ],
    )
    def test_descriptions(self, code, needle):
        assert needle in describe(code)

    def test_unknown_code(self):
        assert "Unknown" in describe(-9999)
        assert "Unknown" in describe(None)
        assert "Unknown" in describe("abc")
