# StikPair Fix v3 — RemotePairing diagnostics (experimental)

The user's original **StikPair.ipa** was inspected: `com.stik.StikPair`, version `1.2.0`, requires **iOS 27.0**, advertises RemotePairing Bonjour service and declares audio/location background modes. Its binary is not modified in place; we rebuild **the original upstream StikPair engine** with a small, auditable Swift patch.

## Build IPA

Open [Actions → Build StikPair Fix v3](../../actions/workflows/build-pairbridge.yml), open the newest **successful** run and download the artifact named `StikPair-Fix-v3-unsigned-IPA`. Unzip the artifact archive; the IPA inside is `StikPair-Fix-v3-unsigned.ipa`.

The build compiles upstream [StikPair](https://github.com/StikDebug/StikPair) pinned to commit `d9661c505130a7b710225fb8ed61128527b46c7e`; source patch is [patches/fix_stikpair_v3.py](patches/fix_stikpair_v3.py).

## Fixes and diagnostics

1. Defaults **Silent audio** to on (while still allowing the user to disable it).
2. Starts the real Rust TCP pairing listener **immediately after Local Network authorization**, instead of deferring the server to a queued background task or a three-second fallback. A late BGContinuedProcessingTask may be attached to the already-running listener.
3. Continues to request a notification whenever the **real PIN callback** arrives.
4. Displays recent milestones while waiting: Local Network authorization, listener ready, Bonjour publish requested, Rust PIN callback. Exports `StikPair-Fix-v3-diagnostics.txt`. **Logs do not include actual PINs, private keys or pairing secrets.**

## On the iPhone

Use Wi-Fi for initial troubleshooting. Import this **unsigned** IPA into LiveContainer 3.8.0; **keep the original StikPair and SideStore installed**. Enable Local Network and notifications for the **LiveContainer host**. For the StikPair Fix app, open its LiveContainer app Settings and try **Fix Local Notification** if PIN notifications fail.

Open StikPair Fix v3, tap **Pair iPhone or iPad**, check the diagnostics. Then open Settings → Privacy & Security → Developer Mode → Pair with StikPair, and look for the real pairing PIN shown via the app or a notification. If there is still no PIN, return to the app and use **Export diagnostic log**. Only share diagnostics; do not share a personal pairing file.

## Important

- This is a **diagnostic build**, not a proven LiveContainer fix.
- LiveContainer does **not** apply guest entitlements to its host app. Guest `UIBackgroundModes` and background-task registration may not be honored exactly as when StikPair is installed natively. An IPA-only change **cannot guarantee** that the host is kept alive after switching to Settings.
- The PIN is emitted **only** after genuine RemotePairing connection callbacks. We do not fabricate a PIN or a `.rppairing`.
- Repo is public: **never upload** certificates, device pairing plist, private keys, provisioning profiles or tokens.
- License: StikPair's non-commercial MIT license; see upstream LICENSE, included in IPA.
