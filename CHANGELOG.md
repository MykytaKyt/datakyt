# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- FastAPI application with CRUD endpoints for employees, offices, projects,
  equipment, equipment parts, furniture, types, software and licenses, with
  search, filtering, sorting and pagination.
- Issue and return endpoints for equipment and furniture, and license seat
  assignment with seat-count and expiry checks.
- Reports: inventory, items per employee, expiring licenses and expiring
  warranties, as JSON, CSV or XLSX.
- CSV/XLSX export of every entity and import with a per-row dry run.
- QR inventory labels as PNG and as an A4 PDF sheet.
- JWT authentication with `admin` and `viewer` roles, and an audit log.
- Server-rendered web UI (Jinja2 + HTMX).
- `datakyt` CLI: `migrate`, `bootstrap`, `seed`, `create-user`, `backup`,
  `restore`, `serve`.
- Docker image and Docker Compose stack; CI with linting, type checking,
  tests against PostgreSQL 16, dependency audit, commit message checks and an
  image build; release workflow publishing to GHCR.
- Contributor documentation: CONTRIBUTING, SECURITY, this changelog.

### Changed

- The schema is now defined by SQLAlchemy models and Alembic migrations.
  Foreign keys are `integer NOT NULL`, money is `numeric(12,2)`, equipment
  status is a Postgres enum, reference tables use `ON DELETE RESTRICT`, and
  every table has `created_at`/`updated_at`.
- Configuration comes from `DATAKYT_*` environment variables.
- Python 3.12 and PostgreSQL 16 are the supported versions.
- `docs/diagram.md` is generated from the models.

### Removed

- `create_table.sql`, `create_database.sql`, `datakyt/_config.py`,
  `requirements.txt` and the QR generator demo, replaced by the above.

### Security

- No hard-coded passwords; the backup command passes the database password
  through the environment instead of the command line.
