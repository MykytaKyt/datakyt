# Contributing to datakyt

Thanks for helping. This page lists the rules every change follows; CI checks
most of them automatically.

## Setup

```sh
make install   # uv sync + pre-commit install (pre-commit and commit-msg hooks)
make lint test
```

Tests need PostgreSQL: either Docker (testcontainers starts `postgres:16-alpine`)
or `DATAKYT_TEST_DATABASE_URL` pointing at a database the tests may wipe.

## Language

Everything in the repository is written in English: code, identifiers,
comments, docstrings, docs, commit messages, issues and pull requests. UI strings
live in `datakyt/web/locales/`; `en.json` is the default and the source of keys.

## Branches and pull requests

- `develop` is the default branch. Work on `feat/<short-name>` or
  `fix/<short-name>` branches and open a pull request against `develop`.
- A pull request needs a green CI run and at least one review before merging.
- Fill in the pull request template: what, why, how it was tested, and the
  checklist (tests, docs, changelog).
- Squash before merging so `develop` has no "WIP" or "fix typo" commits; each
  commit on `develop` is one logical change.

## Commit messages

[Conventional Commits](https://www.conventionalcommits.org/):

```text
type(scope): imperative summary of at most 72 characters

Body wrapped at 72 columns explaining why the change is needed.
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `ci`, `build`, `chore`.

Commits are authored by the developer who makes them (`git config user.name`
and `user.email`). Do not add `Co-Authored-By` lines for AI assistants,
session links, "Generated with" footers or any other tool attribution to
commits, pull request descriptions or code. An assistant may help write the
code, but it does not sign the commit. This is enforced by the `commit-msg`
hook (`ci/commit-msg-attribution.sh`) and in CI (`ci/check-commits.sh`).

## Code style

- `ruff` and `ruff format` with a line length of 100, `mypy --strict` on
  `datakyt/`.
- Type hints on every public function and Google-style docstrings.
- Business rules belong in `datakyt/services/`; routers stay thin. No raw SQL
  outside Alembic migrations.
- Every behavior change comes with tests. Coverage must stay at or above 80%
  overall and at 100% for authentication and assignment logic.

## Database changes

1. Change the models in `datakyt/models/`.
2. `uv run alembic revision --autogenerate -m "short description"`, then read
   and fix the generated file (downgrades too).
3. `make erd` to regenerate `docs/diagram.md`.
4. `make test` runs a migration round trip and checks that the models and
   migrations agree.

## Secrets

Never commit credentials. `.env` is ignored; document new settings in
`.env.example`. `gitleaks` runs in the pre-commit hooks and in CI.

## Releases

1. Move the `Unreleased` entries in `CHANGELOG.md` under a new version heading
   and bump `version` in `pyproject.toml` in a `chore(release): vX.Y.Z` commit.
2. Tag it `vX.Y.Z` and push the tag. The release workflow publishes
   `ghcr.io/mykytakyt/datakyt:X.Y.Z` and a GitHub release with the changelog
   entry.

## Repository settings (maintainers)

Branch protection on `develop`: require a pull request with one approval,
require the `lint`, `test`, `audit`, `commits` and `docker` checks, and block
force pushes and deletions.
