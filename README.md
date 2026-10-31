# StikPair Fix v5 — Experimental LiveContainer RemotePairing repair

This repository rebuilds the **real** StikPair engine (upstream `StikDebug/StikPair`, pinned to commit `d9661c505130a7b710225fb8ed61128527b46c7e`) with auditable changes for running as a guest inside LiveContainer 3.8.0.

## Download

1. Visit [GitHub Actions — Build StikPair Fix v5](../../actions/workflows/build-pairbridge.yml).
2. Select the newest run marked **Success**.
3. Download artifact `StikPair-Fix-v5-unsigned-IPA`.
4. Unzip the downloaded artifact ZIP, then import `StikPair-Fix-v5-unsigned.ipa` into **LiveContainer**. **Do not uninstall SideStore, StikDebug, or your current LiveContainer**.

## What v5 actually fixes

- Starts the Rust TCP listener immediately after verifying Local Network permission rather than relying on a queued background activity.
- Defaults silent-audio background support to on. The user may still turn it off.
- Does **not** stop silent audio or mark pairing as failed automatically when the BGContinuedProcessingTask expires: ending the background task does not prove that the listener has stopped.
- Adds callbacks for **Bonjour DID PUBLISH** / **Bonjour PUBLISH FAILED** using a NetService delegate.
- Records a **REAL TCP CONNECTION ACCEPTED** event directly after Rust `TcpListener.accept()`. This is distinct from a server merely starting successfully.
- Logs when Rust invokes the **REAL PIN CALLBACK**. PIN value, keys and pairing secrets are excluded from the diagnostic log.
- Exports a text log from the waiting screen.

Sources: [v3 patch](patches/fix_stikpair_v3.py), [v4 Bonjour patch](patches/fix_stikpair_v4.py), [v5 TCP and expiry patch](patches/fix_stikpair_v5.py).

## Diagnose the connection

Start StikPair Fix v5 in LiveContainer, enable Silent audio and Location if available, tap **Pair iPhone or iPad**, and keep it visible with LiveContainer Multitask if possible. In iOS Settings → Privacy & Security → Developer Mode → Pair with StikPair, open the pairing screen. Return to the guest app and **Export diagnostic log**.

Interpretation:
- `Rust READY callback`: TCP server bound; **not** proof that Apple connected.
- `Bonjour DID PUBLISH`: advertisement published; **not** proof that system discovery worked.
- `Bonjour PUBLISH FAILED`: advertisement failed; examine error dictionary and host app permissions.
- `REAL TCP CONNECTION ACCEPTED`: Apple connected to TCP listener. If no PIN follows, next investigate the RemotePairing handshake itself.
- `REAL PIN CALLBACK`: use the genuine code shown via StikPair/notification. Do **not** fabricate a code.
- `BG processing expired`: OS terminated the background processing task; continuing normal app code still depends on iOS guest-host behavior.

## Constraints

This is experimental, **not a demonstrated fix** for LiveContainer. LiveContainer guest app entitlements are not automatically applied to the host; even a valid IPA cannot force iOS to keep its host alive. Do not upload personal `.rppairing`, Apple signing keys, device certificates or pairing `.plist` to this public repository.

StikPair is subject to its upstream license, included in the IPA. Unsigned build: install only through LiveContainer or with appropriate code signing; preserve existing working apps.
