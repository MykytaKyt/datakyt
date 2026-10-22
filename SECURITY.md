# Security policy

## Supported versions

Only the latest release receives security fixes.

## Reporting a vulnerability

Please do not open a public issue. Report it privately through
[GitHub security advisories](https://github.com/MykytaKyt/datakyt/security/advisories/new)
with a description, the affected version and steps to reproduce. You should get
an answer within a week. Once a fix is released, the advisory is published with
credit to the reporter unless you prefer otherwise.

## Deployment notes

- Set `DATAKYT_ENV=production` and a random `DATAKYT_JWT_SECRET` of at least 32
  characters; the app refuses to start in production without one.
- Serve the app behind HTTPS. The UI session cookie is `HttpOnly` and
  `SameSite=Strict`, and is marked `Secure` when the request arrives over HTTPS
  (configure your proxy to forward `X-Forwarded-Proto`).
- The Compose file is meant for local use: change the database password and do
  not expose PostgreSQL publicly.
- Backups contain personal data (names, e-mails, phone numbers); store them
  with the same care as the database.
