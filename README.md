# GitHub Repo Analyzer

A command-line tool that fetches and displays a user's top GitHub repositories using the GitHub API. It serves as a non-trivial initial codebase for implementing build automation.


## Usage
```bash
python src/analyzer.py <github_username>
```

## How to replicate the build

### Install dependencies

```bash
poetry install
```

### Generate the project
```bash
poetry build
```

## How to use

### Build the project

Create a dist directory containing the wheel and the compressed archive:
```bash
poetry build
```

### Test the project

```bash
poetry run pytest
```

### Run the project

```bash
poetry run python src/analyzer.py <GitHub_account>
```

## Set up static code analysis

### Install the static code analysers

```bash
poetry add --group dev ruff mypy types-requests
```

### Run the static code analysers

```bash
poetry run ruff check src
poetry run mypy src
```

## Pre-commit hooks that trigger the static code analysis

### Install the pre-commit hook

```bash
poetry add --group dev pre-commit
```

### Run the pre-commit

```bash
poetry run pre-commit install
poetry run pre-commit run --all-files
```

## Unit tests

### Install pytest

```bash
poetry add --group dev pytest
```

### Run pytest

```bash
poetry run pytest -v
```



