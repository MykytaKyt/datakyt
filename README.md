# datakyt

## How to expand PostgreSQL for Linux

- `export PGHOST=localhost`
- `sudo -u postgres psql`
- `postgres=# ALTER USER postgres PASSWORD '12345';`
- `psql -U postgres -d postgres -a -f create_database.sql`
