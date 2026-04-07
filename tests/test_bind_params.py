"""Tests for bind parameter utilities."""

from __future__ import annotations

import pytest

from dtiam.utils.bind_params import (
    extract_bind_params,
    is_parameterized_policy,
    parse_param_strings,
    validate_bind_params,
)


class TestExtractBindParams:
    """Tests for extract_bind_params function."""

    def test_single_param(self) -> None:
        stmt = "ALLOW storage:logs:read WHERE storage:dt.security_context='${bindParam:sec_context}';"
        assert extract_bind_params(stmt) == ["sec_context"]

    def test_multiple_params(self) -> None:
        stmt = (
            "ALLOW storage:logs:read "
            "WHERE storage:gcp.project.id='${bindParam:project_id}' "
            "AND storage:dt.security_context='${bindParam:sec_context}';"
        )
        assert extract_bind_params(stmt) == ["project_id", "sec_context"]

    def test_duplicate_params_deduplicated(self) -> None:
        stmt = "ALLOW x WHERE a='${bindParam:foo}' AND b='${bindParam:foo}';"
        assert extract_bind_params(stmt) == ["foo"]

    def test_no_params(self) -> None:
        stmt = "ALLOW settings:objects:read;"
        assert extract_bind_params(stmt) == []

    def test_empty_string(self) -> None:
        assert extract_bind_params("") == []

    def test_params_sorted(self) -> None:
        stmt = "WHERE z='${bindParam:zebra}' AND a='${bindParam:alpha}';"
        assert extract_bind_params(stmt) == ["alpha", "zebra"]

    def test_param_with_hyphens(self) -> None:
        stmt = "WHERE a='${bindParam:my-param-name}';"
        assert extract_bind_params(stmt) == ["my-param-name"]

    def test_param_with_underscores(self) -> None:
        stmt = "WHERE a='${bindParam:my_param_name}';"
        assert extract_bind_params(stmt) == ["my_param_name"]


class TestIsParameterizedPolicy:
    """Tests for is_parameterized_policy function."""

    def test_parameterized(self) -> None:
        policy = {"statementQuery": "ALLOW x WHERE a='${bindParam:foo}';"}
        assert is_parameterized_policy(policy) is True

    def test_not_parameterized(self) -> None:
        policy = {"statementQuery": "ALLOW settings:objects:read;"}
        assert is_parameterized_policy(policy) is False

    def test_no_statement_query(self) -> None:
        policy = {"name": "test"}
        assert is_parameterized_policy(policy) is False

    def test_empty_statement(self) -> None:
        policy = {"statementQuery": ""}
        assert is_parameterized_policy(policy) is False


class TestParseParamStrings:
    """Tests for parse_param_strings function."""

    def test_single_param(self) -> None:
        assert parse_param_strings(["foo=bar"]) == {"foo": "bar"}

    def test_multiple_params(self) -> None:
        assert parse_param_strings(["a=1", "b=2"]) == {"a": "1", "b": "2"}

    def test_value_with_equals(self) -> None:
        assert parse_param_strings(["key=a=b=c"]) == {"key": "a=b=c"}

    def test_value_with_commas(self) -> None:
        assert parse_param_strings(["zones=zone1,zone2"]) == {"zones": "zone1,zone2"}

    def test_empty_value(self) -> None:
        assert parse_param_strings(["key="]) == {"key": ""}

    def test_invalid_format_no_equals(self) -> None:
        with pytest.raises(ValueError, match="Invalid parameter format"):
            parse_param_strings(["no-equals-sign"])

    def test_empty_key(self) -> None:
        with pytest.raises(ValueError, match="Empty parameter name"):
            parse_param_strings(["=value"])

    def test_empty_list(self) -> None:
        assert parse_param_strings([]) == {}

    def test_whitespace_trimmed(self) -> None:
        assert parse_param_strings(["  key  =  value  "]) == {"key": "value"}


class TestValidateBindParams:
    """Tests for validate_bind_params function."""

    def test_all_provided(self) -> None:
        policy = {"statementQuery": "WHERE a='${bindParam:foo}' AND b='${bindParam:bar}';"}
        missing, extra = validate_bind_params(policy, {"foo": "1", "bar": "2"})
        assert missing == []
        assert extra == []

    def test_missing_params(self) -> None:
        policy = {"statementQuery": "WHERE a='${bindParam:foo}' AND b='${bindParam:bar}';"}
        missing, extra = validate_bind_params(policy, {"foo": "1"})
        assert missing == ["bar"]
        assert extra == []

    def test_extra_params(self) -> None:
        policy = {"statementQuery": "WHERE a='${bindParam:foo}';"}
        missing, extra = validate_bind_params(policy, {"foo": "1", "baz": "2"})
        assert missing == []
        assert extra == ["baz"]

    def test_both_missing_and_extra(self) -> None:
        policy = {"statementQuery": "WHERE a='${bindParam:foo}' AND b='${bindParam:bar}';"}
        missing, extra = validate_bind_params(policy, {"bar": "1", "baz": "2"})
        assert missing == ["foo"]
        assert extra == ["baz"]

    def test_non_parameterized_policy_with_params(self) -> None:
        policy = {"statementQuery": "ALLOW settings:objects:read;"}
        missing, extra = validate_bind_params(policy, {"foo": "1"})
        assert missing == []
        assert extra == ["foo"]

    def test_non_parameterized_policy_no_params(self) -> None:
        policy = {"statementQuery": "ALLOW settings:objects:read;"}
        missing, extra = validate_bind_params(policy, {})
        assert missing == []
        assert extra == []

    def test_parameterized_policy_no_params(self) -> None:
        policy = {"statementQuery": "WHERE a='${bindParam:foo}';"}
        missing, extra = validate_bind_params(policy, {})
        assert missing == ["foo"]
        assert extra == []
