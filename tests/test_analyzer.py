"""Unit tests for the GitHub Repository Analyzer."""

import logging
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.analyzer import fetch_repos, get_top_repos, main


def test_get_top_repos_sorts_and_limits() -> None:
    """Verify that get_top_repos sorts descending by stars and caps at limit."""
    sample_repos: list[dict[str, Any]] = [
        {"name": f"repo-{i}", "stargazers_count": i * 10} for i in range(15)
    ]

    top_10 = get_top_repos(sample_repos, limit=10)

    assert len(top_10) == 10
    assert top_10[0]["name"] == "repo-14"
    assert top_10[0]["stargazers_count"] == 140
    assert top_10[-1]["name"] == "repo-5"


@patch("src.analyzer.requests.get")
def test_fetch_repos_success(mock_get: MagicMock) -> None:
    """Verify fetch_repos returns parsed repository list on HTTP 200."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"X-RateLimit-Remaining": "59"}
    mock_response.json.return_value = [
        {"name": "alpha", "stargazers_count": 42, "language": "Python"}
    ]
    mock_get.return_value = mock_response

    repos = fetch_repos("octocat")

    assert len(repos) == 1
    assert repos[0]["name"] == "alpha"
    mock_get.assert_called_once_with(
        "https://api.github.com/users/octocat/repos", timeout=10
    )


@patch("src.analyzer.requests.get")
def test_fetch_repos_not_found_raises_value_error(
    mock_get: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify HTTP 404 logs an ERROR and raises ValueError."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.headers = {}
    mock_get.return_value = mock_response

    with caplog.at_level(logging.ERROR), pytest.raises(ValueError, match="not found"):
        fetch_repos("ghost-user")

    assert any(record.levelno == logging.ERROR for record in caplog.records)


@patch("src.analyzer.requests.get")
def test_fetch_repos_invalid_payload_logs_critical(
    mock_get: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify non-list JSON payload logs CRITICAL and raises ValueError."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_response.json.return_value = {"message": "unexpected object"}
    mock_get.return_value = mock_response

    with (
        caplog.at_level(logging.CRITICAL),
        pytest.raises(ValueError, match="Unexpected API response"),
    ):
        fetch_repos("octocat")

    assert any(record.levelno == logging.CRITICAL for record in caplog.records)


@patch("src.analyzer.requests.get")
def test_fetch_repos_network_error(mock_get: MagicMock) -> None:
    """Verify network failure propagates requests.RequestException."""
    mock_get.side_effect = requests.ConnectionError("Network unreachable")

    with pytest.raises(requests.RequestException):
        fetch_repos("octocat")


@patch("src.analyzer.fetch_repos")
def test_main_empty_repos_logs_warning(
    mock_fetch: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify main exits cleanly with 0 and logs a WARNING when user has no repos."""
    mock_fetch.return_value = []

    with caplog.at_level(logging.WARNING):
        exit_code = main(["emptyuser"])

    assert exit_code == 0
    assert any(record.levelno == logging.WARNING for record in caplog.records)


def test_main_missing_argument_returns_error_code() -> None:
    """Verify main returns exit code 1 when no username argument is passed."""
    assert main([]) == 1
