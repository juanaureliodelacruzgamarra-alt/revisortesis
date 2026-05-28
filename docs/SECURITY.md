# SECURITY — KIMY

Resumen de auditoría de seguridad y postura actual del sistema. **Estado:** desarrollo, antes de exposición pública. Use este documento como check-list previo a deploy en producción.

## OWASP Top 10 (2021) — postura actual

| ID | Riesgo | Estado | Notas |
|----|--------|--------|-------|
| A01 | Broken Access Control | ✅ Cubierto | `require_roles(...)` en routers + `submissions_service.can_access()` por avance + middleware web por path. Test boundary suite (`test_auth.py::test_*_cannot_access_*`) cubre los cruces críticos. |
| A02 | Cryptographic Failures | ⚠️ Parcial | Tokens ORCID y Copyleaks key cifrados con Fernet (AES-128-CBC + HMAC) vía [core/crypto.py](apps/api/src/kimy/core/crypto.py). Passwords con Argon2id. **Falta:** secretos por variable de entorno en prod (no en `.env` versionado); rotación periódica del `ENCRYPTION_KEY` no soportada. |
| A03 | Injection | ✅ Cubierto | SQLAlchemy 2.0 con bind params en todas las consultas. No string-format SQL. Inputs validados por Pydantic v2 antes del service layer. |
| A04 | Insecure Design | ⚠️ Parcial | Pipeline IA acepta documentos no confiables — los pasamos por extracción local (pypdf/python-docx) sin sandboxing. **Falta:** límite explícito de RAM por job, virus scan opcional (clamav). |
| A05 | Security Misconfiguration | ⚠️ Parcial | Security headers añadidos en [main.py](apps/api/src/kimy/main.py): X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, HSTS (HTTPS). CORS con allowlist explícita. **Falta:** CSP estricta. |
| A06 | Vulnerable Components | ⚠️ Pendiente | Sin Dependabot / Renovate aún. Recomendado: GitHub Dependabot semanal + `pip-audit` y `pnpm audit --prod` en CI. |
| A07 | Auth Failures | ✅ Cubierto | Rate limit `5/min` en login/register, `20/min` en refresh ([core/rate_limit.py](apps/api/src/kimy/core/rate_limit.py)). JWT HS256 con secret ≥ 32 bytes. Refresh token con `type=refresh` validado por separado. |
| A08 | Software & Data Integrity | ⚠️ Parcial | Documentos firmados con SHA-256 al subir; no hay verificación de firma criptográfica de actas PDF (sería deseable: PDF signing). |
| A09 | Logging & Monitoring | ⚠️ Pendiente | Logs por `logging` estándar, sin SIEM. **Falta:** tabla `audit_logs` ya modelada en IMPLEMENTATION.md pero no llena automáticamente. |
| A10 | SSRF | ✅ Cubierto | El cliente CrossRef y ORCID usan hostnames fijos, no aceptan URL del usuario. Downloads de plantillas/versiones se sirven desde `storage/` con `storage.resolve()` que previene path traversal. |

## Controles activos

### Autenticación
- **Hash**: Argon2id vía `argon2-cffi` (default profile)
- **JWT**: HS256, access 15 min, refresh 30 días. Token `type` distinto por endpoint
- **Token storage**:
  - Web: cookie HttpOnly + SameSite=lax + Secure (cuando NODE_ENV=production)
  - Mobile: `expo-secure-store` (Keychain en iOS, EncryptedSharedPreferences en Android)
  - API: header `Authorization: Bearer …`

### Autorización
- `require_roles(UserRole.x, …)` decorator en endpoints sensibles
- `submissions_service.can_access(submission, user)` por documento (estudiante ve los suyos; asesor ve los asignados; coordinador/admin ven todo)
- Middleware web (`apps/web/src/middleware.ts`) bloquea rutas `/student|/advisor|/coordinator|/admin` sin cookie

### Validación de input
- Pydantic v2 en el API (rechazos automáticos → 422)
- Zod planeado para los formularios web; hoy hay validación HTML5 + RHF en formularios críticos
- Mime type + size cap (50 MB) en uploads de avances y plantillas

### Rate limiting
| Endpoint | Límite |
|---|---|
| `POST /api/v1/auth/login` | 5/min por IP |
| `POST /api/v1/auth/register` | 5/min por IP |
| `POST /api/v1/auth/refresh` | 20/min por IP |
| (Default global) | 120/min por IP |

Desactivado en tests con `RATE_LIMIT_DISABLED=1`.

### Headers de seguridad
Aplicados por `SecurityHeadersMiddleware`:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: no-referrer
Permissions-Policy: geolocation=(), microphone=(), camera=()
Strict-Transport-Security: max-age=31536000; includeSubDomains   # solo en HTTPS
```

### Tokens externos
- **ORCID** (access + refresh): cifrados Fernet en `advisor_profiles`
- **Copyleaks API key** (cuando exista): vivirá en `system_settings.copyleaks_api_key` cifrado

### CORS
Allowlist explícita en `Settings.cors_origins`. Default dev: `http://localhost:3000`. En producción, hay que setear la URL del web vía env y desactivar `allow_credentials` si se cambia a wildcard.

## Cosas que NO están implementadas todavía

| Brecha | Riesgo si se ignora | Mitigación recomendada |
|---|---|---|
| Audit log automático para mutaciones | Investigaciones forenses pierden trazabilidad | Cablear middleware que inserte en `audit_logs` por `request.method != GET` |
| 2FA / TOTP | Cuenta comprometida si la contraseña fuga | Añadir `users.totp_secret` + endpoint `/auth/verify-totp` |
| Política de contraseñas más estricta | Brute force lento pero posible | Hoy: ≥ 8 chars. Subir a 12 + zxcvbn check |
| Revocación de JWT | Tokens robados válidos hasta exp | Tabla de jti revocados o pasar a sessions server-side |
| CSP estricta para web | XSS de terceros vía dependencias | `Content-Security-Policy` en `next.config.ts` headers |
| Scan SAST en CI | Vulnerabilidades de código nuevas | Añadir `semgrep` o `bandit` |
| Scan SCA / dependencias | CVEs en transitivas | Dependabot + `pip-audit` en CI |
| Backups encriptados de Postgres | Pérdida total / leak | `pg_dump` periódico cifrado con GPG hacia S3 con KMS |
| WAF / DDoS | Saturación trivial | Cloudflare o equivalente delante del API |

## Reporte de vulnerabilidades

Si encontraste un problema, no abras un issue público. Envía un email a `homodeus.cith@gmail.com` con:

- Pasos para reproducir
- Versión / commit afectado
- Estimación de impacto

Confirmaremos recepción en 72 h.

## Antes de deploy en producción — checklist

- [ ] `JWT_SECRET` y `ENCRYPTION_KEY` rotados, ≥ 32 bytes, NO en repo
- [ ] `CORS_ORIGINS` apunta solo al dominio del web de prod
- [ ] DB con conexión TLS exigida (`sslmode=require`)
- [ ] `ORCID_SANDBOX=false`, credenciales reales de orcid.org
- [ ] `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` rotables (clave dedicada al proyecto)
- [ ] Rate limit endurecido si hay backend público (cambiar de IP-keyed a IP+user)
- [ ] HTTPS terminator delante (`HSTS` activo)
- [ ] Backups Postgres + pgvector configurados
- [ ] Dependabot habilitado
- [ ] Política RGPD/Habeas Data revisada con DPO de la institución (estamos almacenando datos personales de estudiantes y asesores)
