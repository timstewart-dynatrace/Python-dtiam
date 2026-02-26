"""Bind parameter utilities for parameterized IAM policies.

Provides helpers for extracting ${bindParam:name} placeholders from
policy statement queries and parsing KEY=VALUE parameter strings.
"""

from __future__ import annotations

import re
from typing import Any

# Pattern to match ${bindParam:param_name} in policy statement queries
BIND_PARAM_PATTERN = re.compile(r"\$\{bindParam:([^}]+)\}")


def extract_bind_params(statement_query: str) -> list[str]:
    """Extract bind parameter names from a policy statement query.

    Args:
        statement_query: Policy statement query string

    Returns:
        Sorted, deduplicated list of parameter names found
    """
    params = set(BIND_PARAM_PATTERN.findall(statement_query))
    return sorted(params)


def is_parameterized_policy(policy: dict[str, Any]) -> bool:
    """Check whether a policy uses bind parameters.

    Args:
        policy: Policy dictionary with optional 'statementQuery' key

    Returns:
        True if the policy's statement query contains ${bindParam:...} placeholders
    """
    statement = policy.get("statementQuery", "")
    return bool(BIND_PARAM_PATTERN.search(statement))


def parse_param_strings(param_strings: list[str]) -> dict[str, str]:
    """Parse a list of KEY=VALUE strings into a parameters dictionary.

    Args:
        param_strings: List of "key=value" strings

    Returns:
        Dictionary mapping parameter names to values

    Raises:
        ValueError: If any string is not in KEY=VALUE format
    """
    parameters: dict[str, str] = {}
    for param_str in param_strings:
        if "=" not in param_str:
            raise ValueError(
                f"Invalid parameter format: '{param_str}'. Use KEY=VALUE format."
            )
        key, value = param_str.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"Empty parameter name in: '{param_str}'")
        parameters[key] = value
    return parameters


def validate_bind_params(
    policy: dict[str, Any],
    provided_params: dict[str, str],
) -> tuple[list[str], list[str]]:
    """Validate provided parameters against a policy's bind parameters.

    Args:
        policy: Policy dictionary with 'statementQuery'
        provided_params: Parameters dict from the user

    Returns:
        Tuple of (missing_params, extra_params) -- both are lists of param names
    """
    required = set(extract_bind_params(policy.get("statementQuery", "")))
    provided = set(provided_params.keys())
    missing = sorted(required - provided)
    extra = sorted(provided - required)
    return missing, extra
