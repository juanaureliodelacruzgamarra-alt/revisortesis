---
name: kimy-test
description: Run the full KIMY check suite — API pytest, web typecheck, web lint — and report failures with file paths. Use before committing or before opening a PR.
allowed-tools: Bash
---

# Run KIMY checks

Execute these three checks **in parallel** from the repo root and consolidate results. If any step fails, surface the failing file and line.

## 1. Backend tests (pytest)

```bash
cd "/c/Users/Crishtian Paz/Desktop/UNT/ciclo 2026-1/Tesis 1/REVISIONTESIS/apps/api" && py -3.12 -m uv run --active -- pytest -q
```

## 2. Web typecheck (tsc)

```bash
cd "/c/Users/Crishtian Paz/Desktop/UNT/ciclo 2026-1/Tesis 1/REVISIONTESIS" && pnpm --filter @kimy/web typecheck
```

## 3. Web lint (ESLint)

```bash
cd "/c/Users/Crishtian Paz/Desktop/UNT/ciclo 2026-1/Tesis 1/REVISIONTESIS" && pnpm --filter @kimy/web lint
```

## Reporting

- If **all three pass**: respond with a single line `✓ All checks passed`.
- If **any fail**:
  - List failures grouped by tool (pytest / typecheck / lint).
  - For each failure, include the file path and line number when the tool provides one.
  - Do NOT auto-fix anything unless the user explicitly asks.
