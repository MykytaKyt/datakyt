# datakyt — assistant rules

- All code, comments, docs and commit messages are in English.
- Commit messages follow Conventional Commits; the author is the human developer.
- Never add Co-Authored-By, session links or any AI attribution to commits or PRs.
  This includes Claude-Session lines and "Generated with" footers in commit
  messages, PR descriptions and code.
- Run `make lint test` before proposing a commit.
- Business rules live in `datakyt/services/`; schema changes go through Alembic
  migrations followed by `make erd`.
