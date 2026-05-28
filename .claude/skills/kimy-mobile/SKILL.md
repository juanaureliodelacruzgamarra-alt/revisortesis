---
name: kimy-mobile
description: Start the KIMY Expo app (apps/mobile) for testing on a phone or emulator. Prereqs the API is reachable. Use when the user wants to test the mobile experience.
allowed-tools: Bash
---

# Start KIMY mobile (Expo)

Pre-flight: the API must respond on the host's API URL. If `pnpm api:dev` isn't running, tell the user to run `/kimy-up` first.

```bash
curl -sf http://localhost:8005/health >/dev/null && echo "API up" || echo "API down — run /kimy-up first"
```

If API down, stop and tell the user.

## Start Expo

From the repo root:

```bash
cd "/c/Users/Crishtian Paz/Desktop/UNT/ciclo 2026-1/Tesis 1/REVISIONTESIS"
pnpm --filter @kimy/mobile start
```

Run this with `run_in_background: true`. It opens an interactive Metro bundler. The user scans the QR code with Expo Go (iOS / Android) or presses `a`/`i` for emulators.

## Network gotchas

- **Android emulator** (Studio): the API URL `http://10.0.2.2:8005` already points to the host — no change.
- **Physical device on the same Wi-Fi**: replace `10.0.2.2` with the host's LAN IP. Edit `apps/mobile/app.json` `extra.apiUrl` OR set `EXPO_PUBLIC_API_URL` before starting.
- **iOS simulator**: `http://localhost:8005` works.

## Report

Print:
```
✓ Metro bundler running. Scan the QR with Expo Go,
  or press `a` (Android), `i` (iOS), or `w` (web).
```
