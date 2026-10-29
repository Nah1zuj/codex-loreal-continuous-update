# TRACE hardware reference subsystem

Hardware architecture and simulator implemented; physical device integration not yet validated.

Independent Python package (`src/trace_hardware`), standard library only. No LLM,
image processing, browser or web-framework imports. Core contracts: capability
discovery, adapter lifecycle, camera/display/audio/lighting/assistive input;
Gateway: registry, explicit pairing, permissions, typed events and session binding.
The existing backend has a thin `/api/hardware` HTTP bridge. It still owns all
coaching intelligence. If this optional package is absent, existing routes work.

From repository root: `python -m pip install -e hardware`. Restart existing backend.
Tests: `python -m pytest tests/test_hardware.py -o addopts='' -q`.
Independent import: `python -c "from trace_hardware.core import Gateway, Simulator"`.
No credentials or `.env` changes required. Python >=3.11.

## Browser mirror (H1)

1. Start a normal TRACE text/voice session.
2. Open Devices `/devices`. Explicitly generate a read-only pairing code.
3. In your authorized browser reference display `/mirror`, enter it within 120s.
4. The client discovers the negotiated display-only capability and synchronizes
   actual canonical step, workflow and completed/total count every two seconds.
5. Disconnect in either client; owner can revoke. Reconnect requires new pairing.

The reference adapter is a real HTTP display client, **not** a commercial mirror
SDK. No camera/microphone grant is negotiated. Neither raw vision frames, full
chat, saved profile nor memory are transferred. Overlays require future authorized
camera adapters, not made-up detections. Original web camera controls remain intact.

Code has 96 random bits, one use, RAM only, expiry120s. Device token has256 random
bits; only hash server-side, token RAM client-side, never URLs/localStorage.
Display permission lease30min, heartbeat expiry5min; hidden/unmounted/reloaded
clients lose access. Max100 devices/codes, max3 open codes per owner, simulator idle RAM expiry15min, audit200
metadata entries/24h, expired devices purged15min later. Restart drops all pairing.
Only HTTPS outside loopback development; don't trust arbitrary forwarded headers.
Existing anonymous HttpOnly browser identity scopes owner APIs; production account
authentication, managed TLS, durable pairing, audit persistence and load/rate-limit
hardening are future deployment prerequisites. This is a localhost prototype.

## Events / safety boundary

`Event`: device_id, session_id, timestamp, event_type, validated payload,
permission_status, monotonic sequence. Device token binding prevents impersonation;
timestamps +/-30s, replay rejection. Reference mirror accepts lifecycle events with
empty payload only. Camera/audio/lighting/button/haptic events require a future
server grant and adapter; they are rejected, never routed to LLM tools. 4kB hardware
request limit. No media transfer or recording endpoint. Poll timeout8s with AbortSignal;
failed reads clear client state and disconnect. Owner revoke acts on next poll.

## Simulator / H0, H3

`Simulator` uses deterministic states: connection, display text, audio event,
camera capability (no capture), lighting, buttons, disconnect. Every response states
`simulated:true`. Lighting requires explicit simulator consent, brightness0–100,
temperature2700–6500K, connected state; returned status verifies **simulation only**.
No physical commands. Audio events don't record/play real audio; buttons don't
advance a real plan. Tests use synthetic fixtures, not makeup accuracy evaluation.

`UnsupportedAdapter` is a lifecycle boundary for separate Home Assistant, Matter,
MQTT, BLE, USB/network-camera, microphone/speaker and haptic adapters. `connect()`
raises unsupported; empty capabilities, disconnected state. Optional interfaces
allow incremental concrete implementations. HTTP is the only reference transport.
MQTT topics, BLE characteristics, WebSocket authentication, network camera media,
vendor SDK credentials and device allowlists need specific authorized equipment.
H2/H4 skipped by design: no endpoint/hardware/SDK supplied. No speculative physical
connectivity, arbitrary device URLs or unrestricted natural-language commands.

## Provenance

Hardware code is original, no downloaded device SDK. UI retains existing React/Vite,
[Three.js](https://github.com/mrdoob/three.js) for BufferGeometry/Points/shaders,
[GSAP](https://github.com/greensock/GSAP) existing motion, locally bundled licensed
Cormorant/Song fonts. Existing dependencies chosen to preserve app without migration
or redundant animation packages. Geometry/apple/category illustrations are original.
No new third-party portrait/model, no Apple Inc logo; replace optional human.glb
only with a model you own or with a verified permissive license.
