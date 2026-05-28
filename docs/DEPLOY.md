# Deploy — KIMY

Guía para llevar KIMY de tu laptop a un servidor de la universidad. Asume que tienes acceso SSH a una VM Linux con Docker 24+, ~4 GB RAM, ~20 GB disco.

## 1. Pre-requisitos en el servidor

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin git
sudo usermod -aG docker $USER     # luego cierra sesión y vuelve a entrar
docker --version                  # >= 24
docker compose version            # v2.20+
```

Verifica que el firewall permite 80/443 si vas a poner Caddy/Traefik delante. Por ahora deja `kimy-api` y `kimy-web` solo accesibles vía la red interna de Docker.

## 2. Clonar el repo

```bash
git clone https://github.com/CrishPaz/RevisorTesis.git /opt/kimy
cd /opt/kimy
```

## 3. Generar secretos

KIMY necesita 3 secretos críticos. Genera valores reales — los del `.env.prod.example` son placeholders.

```bash
# JWT signing key (mínimo 32 bytes para HS256)
echo "JWT_SECRET=$(openssl rand -base64 48)"

# Fernet key para tokens ORCID en reposo
echo "ENCRYPTION_KEY=$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"

# Postgres password
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)"
```

Copia el template + edítalo:

```bash
cp infra/.env.prod.example infra/.env.prod
$EDITOR infra/.env.prod
```

Pega los 3 secretos generados, rellena `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` si las tienes, configura `ORCID_*` para la app de producción, ajusta `CORS_ORIGINS` y `NEXT_PUBLIC_API_URL` a tus dominios reales.

> Verificación: `grep -c CHANGE_ME infra/.env.prod` debe devolver **0**. Si no, alguien dejó placeholders.

## 4. Build + start

```bash
docker compose -f infra/docker-compose.prod.yml --env-file infra/.env.prod build --pull
docker compose -f infra/docker-compose.prod.yml --env-file infra/.env.prod up -d
```

El healthcheck de `api` arranca su loop tras 20s; `db` necesita unos 10s para aceptar conexiones. La migración Alembic corre automáticamente al arrancar el container (ver `apps/api/Dockerfile::CMD`).

Verifica:

```bash
docker compose -f infra/docker-compose.prod.yml ps
docker compose -f infra/docker-compose.prod.yml logs -f api
```

Health interno:

```bash
docker exec kimy-api curl -fsS http://localhost:8000/health
docker exec kimy-web curl -fsS http://localhost:3000/
```

## 5. Reverse proxy (TLS)

Hasta que pongas un terminador HTTPS delante, los servicios solo se ven dentro de la red de Docker. Recomendación: **Caddy** por auto-HTTPS con Let's Encrypt.

`infra/Caddyfile`:

```
kimy.example.edu.pe {
    encode gzip
    reverse_proxy kimy-web:3000
}

api.kimy.example.edu.pe {
    encode gzip
    reverse_proxy kimy-api:8000
}
```

Descomenta el servicio `caddy` en `docker-compose.prod.yml`, abre 80/443 en el firewall, y haz `docker compose up -d caddy`. Caddy resolverá los certificados solo la primera vez que se llame al dominio.

## 6. Backups

Postgres es donde vive todo lo crítico (usuarios, avances, evaluaciones, ORCID tokens cifrados, audit logs). Programa un cron en el host:

```bash
# /etc/cron.d/kimy-backup
0 3 * * * root docker exec kimy-db pg_dump -U $POSTGRES_USER $POSTGRES_DB | gpg --encrypt -r backups@example.edu.pe > /var/backups/kimy/$(date +\%F).sql.gpg
```

Y un cron para limpiar > 30 días:
```bash
0 4 * * * root find /var/backups/kimy -name '*.sql.gpg' -mtime +30 -delete
```

El volumen `kimy-storage` contiene los archivos subidos (plantillas, avances, datasets FT). Snapshot vía `tar -czf` o respáldalo a S3/MinIO desde otro cron.

## 7. Rotación de secretos

| Secreto | Cuándo rotar | Cómo |
|---|---|---|
| `JWT_SECRET` | Trimestralmente; inmediatamente si fuga | Cambia y reinicia API. **Todos los sessions activos quedan invalidados** — esperado. |
| `ENCRYPTION_KEY` | Anualmente | Más complejo: requiere re-cifrar `advisor_profiles.orcid_*_token_enc`. Implementar script de migración antes de rotar. |
| `POSTGRES_PASSWORD` | Anualmente | Actualiza `.env.prod`, `docker compose up -d --no-deps db`, conecta y `ALTER USER`. |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | Cuando se sospeche fuga | Hot-reloadeable: edita `.env.prod` y `docker compose up -d --no-deps api`. |

## 8. Actualización a una nueva versión

```bash
cd /opt/kimy
git fetch && git pull origin main
docker compose -f infra/docker-compose.prod.yml --env-file infra/.env.prod build --pull
docker compose -f infra/docker-compose.prod.yml --env-file infra/.env.prod up -d
```

La migración Alembic corre automáticamente al arrancar `api`. Si una migración es destructiva, hazle un `pg_dump` antes.

Rollback de imagen (si la nueva versión rompe):
```bash
IMAGE_TAG=$(git rev-parse --short HEAD~1) docker compose ... up -d
```

## 9. Observabilidad

KIMY emite logs JSON-friendly por stdout. Configura:
- `docker compose logs` para inspección rápida
- Loki + Grafana para retención y queries (recomendado en prod)
- El endpoint `GET /api/v1/admin/audit` ya da trazabilidad por mutación (rol admin)

## 10. Checklist pre-launch

- [ ] `grep CHANGE_ME infra/.env.prod` no devuelve nada
- [ ] `ORCID_SANDBOX=false` con credenciales reales
- [ ] `NEXT_PUBLIC_API_URL` apunta al dominio HTTPS público
- [ ] `CORS_ORIGINS` solo incluye el dominio del web (no `*`)
- [ ] HTTPS terminator (Caddy/Traefik) corriendo y certificados emitidos
- [ ] `docker exec kimy-api curl /health` → 200
- [ ] Login + upload de un avance de prueba → evaluación IA aparece
- [ ] Backup nocturno configurado y testeado (restaurar desde último dump en una VM aparte)
- [ ] Dependabot habilitado en GitHub (`.github/dependabot.yml` ya está)
- [ ] Monitoreo de uptime apuntando a `https://kimy.example.edu.pe/` y `https://api.kimy.example.edu.pe/health`
- [ ] Política RGPD/Habeas Data revisada con DPO institucional

Ver también [docs/SECURITY.md](SECURITY.md) para la auditoría OWASP completa.
