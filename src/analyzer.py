"""GitHub Repository Analyzer CLI.

Fetches public repositories for a given GitHub user and displays
the top 10 repositories ranked by star count.
"""

import logging
import sys
from typing import Any

import requests
from rich.console import Console
from rich.table import Table

logger = logging.getLogger(__name__)


def configure_logging(verbose: bool = False) -> None:
    """Configure application logging with level-based formatting.

    Args:
        verbose: If True, sets the logging threshold to DEBUG; otherwise INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def fetch_repos(username: str) -> list[dict[str, Any]]:
    """Fetch all public repositories for a GitHub user via the REST API.

    Args:
        username: The GitHub account login name.

    Returns:
        A list of repository dictionaries returned by the GitHub API.

    Raises:
        ValueError: If the user does not exist (HTTP 404) or returns invalid JSON.
        requests.RequestException: If a network or unexpected HTTP error occurs.
    """
    url = f"https://api.github.com/users/{username}/repos"
    logger.debug("Sending GET request to GitHub API: %s", url)

    try:
        response = requests.get(url, timeout=10)
    except requests.RequestException as exc:
        logger.error("Network failure while querying GitHub API: %s", exc)
        raise

    logger.debug("Received HTTP %d from GitHub API", response.status_code)

    remaining = response.headers.get("X-RateLimit-Remaining")
    if remaining is not None and int(remaining) < 5:
        logger.warning(
            "GitHub API rate limit nearly exhausted (%s requests remaining).",
            remaining,
        )

    if response.status_code == 404:
        logger.error("GitHub user '%s' was not found (HTTP 404).", username)
        raise ValueError(f"GitHub user '{username}' not found.")

    response.raise_for_status()

    try:
        data: Any = response.json()
    except ValueError as exc:
        logger.critical("Corrupted non-JSON payload received from GitHub API.")
        raise ValueError("Invalid JSON response from GitHub API.") from exc

    if not isinstance(data, list):
        logger.critical(
            "Unexpected payload type '%s'; expected a list of repositories.",
            type(data).__name__,
        )
        raise ValueError("Unexpected API response structure.")

    logger.debug("Retrieved %d raw repositories for '%s'.", len(data), username)
    return data


def get_top_repos(repos: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    """Sort repositories by stargazers count in descending order.

    Args:
        repos: List of repository metadata dictionaries.
        limit: Maximum number of top repositories to return.

    Returns:
        A slice containing up to `limit` top-starred repositories.
    """
    sorted_repos = sorted(
        repos,
        key=lambda repo: int(repo.get("stargazers_count", 0)),
        reverse=True,
    )
    return sorted_repos[:limit]


def display_repos(username: str, repos: list[dict[str, Any]]) -> None:
    """Render a formatted Rich table of repositories to the terminal.

    Args:
        username: The GitHub account login name displayed in the table title.
        repos: The list of repositories to display.
    """
    console = Console()
    table = Table(title=f"Top {len(repos)} GitHub Repositories for {username}")
    table.add_column("Name", style="cyan")
    table.add_column("Stars", justify="right", style="magenta")
    table.add_column("Language", style="green")

    for repo in repos:
        table.add_row(
            str(repo.get("name", "N/A")),
            str(repo.get("stargazers_count", 0)),
            str(repo.get("language") or "N/A"),
        )

    console.print(table)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI entry point.

    Args:
        argv: Optional list of CLI arguments (defaults to sys.argv[1:]).

    Returns:
        Exit status code (0 on success, 1 on error).
    """
    args = sys.argv[1:] if argv is None else argv
    verbose = "--verbose" in args or "-v" in args
    positional = [arg for arg in args if arg not in ("--verbose", "-v")]

    configure_logging(verbose=verbose)

    if not positional:
        logger.error("Missing required <github_username> CLI argument.")
        print("Usage: python src/analyzer.py <github_username> [--verbose]")
        return 1

    username = positional[0]
    logger.info("Starting repository analysis for GitHub user '%s'.", username)

    try:
        repos = fetch_repos(username)
    except (ValueError, requests.RequestException) as exc:
        logger.error("Analysis aborted for '%s': %s", username, exc)
        return 1

    if not repos:
        logger.warning("User '%s' has no public repositories to display.", username)
        return 0

    top_repos = get_top_repos(repos, limit=10)
    logger.info(
        "Displaying top %d repositories (out of %d) for '%s'.",
        len(top_repos),
        len(repos),
        username,
    )
    display_repos(username, top_repos)
    return 0


if __name__ == "__main__":
    sys.exit(main())
