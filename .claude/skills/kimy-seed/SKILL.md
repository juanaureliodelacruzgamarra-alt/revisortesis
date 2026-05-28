---
name: kimy-seed
description: Create one test user per role (student, advisor, coordinator, admin) plus one academic program. Idempotent — skips users that already exist (409 conflict). Use after kimy-up on a fresh DB to have working credentials.
allowed-tools: Bash
---

# Seed KIMY test data

Hits the API at `http://localhost:8003`. **Pre-flight:** verify it responds before doing anything:

```bash
curl -sf http://localhost:8003/health >/dev/null && echo "API up" || echo "API down — run /kimy-up first"
```

If the API is down, stop and tell the user to run `/kimy-up`.

## 1. Create users (4 roles)

For each user, POST to `/api/v1/auth/register`. A 409 means the user already exists — that's fine, keep going.

| Email | Password | Full name | Role |
|---|---|---|---|
| `admin@unt.edu.pe` | `AdminPass123` | Admin KIMY | admin |
| `coord@unt.edu.pe` | `CoordPass123` | Coordinador KIMY | coordinator |
| `asesor@unt.edu.pe` | `AsesorPass123` | Asesor KIMY | advisor |
| `alumno@unt.edu.pe` | `SuperSecure123` | Alumno KIMY | student |

Example for one:
```bash
curl -s -w "\nHTTP %{http_code}\n" -X POST http://localhost:8003/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@unt.edu.pe","password":"AdminPass123","full_name":"Admin KIMY","role":"admin"}'
```

Treat HTTP 201 or 409 as success; anything else is a failure to report.

## 2. Create a default academic program (skip if any program exists)

Login as admin to get a token, then list programs:

```bash
TOKEN=$(curl -s -X POST http://localhost:8003/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@unt.edu.pe","password":"AdminPass123"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl -s http://localhost:8003/api/v1/programs -H "Authorization: Bearer $TOKEN"
```

If the list is empty (`[]`), create one:
```bash
curl -s -X POST http://localhost:8003/api/v1/programs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data-raw '{"name":"Maestria en Ingenieria de Software","code":"MIS","level":"masters"}'
```

(Use ASCII-only JSON to avoid Git Bash cp1252 mangling on Windows.)

## Final report

Print:
```
Users (login with these on http://localhost:3000/login):
  admin@unt.edu.pe / AdminPass123        → /admin
  coord@unt.edu.pe / CoordPass123        → /coordinator
  asesor@unt.edu.pe / AsesorPass123      → /advisor
  alumno@unt.edu.pe / SuperSecure123     → /student

Program: [MIS] Maestria en Ingenieria de Software (masters)
```
