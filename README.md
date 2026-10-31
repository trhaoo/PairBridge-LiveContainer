# PairBridge for LiveContainer (experimental)

This repository builds an **unsigned iOS IPA** by compiling the **real StikPair Rust RemotePairing engine** and the upstream Swift app, with a PairBridge display name and an always-attempted notification when the genuine pairing PIN arrives.

## Build
Go to [GitHub Actions](../../actions/workflows/build-pairbridge.yml), select the latest successful run and download the `PairBridge-unsigned-IPA` artifact. Unzip the downloaded artifact ZIP to obtain `PairBridge-unsigned.ipa`.

The build uses GitHub-hosted **Xcode 27**, Rust iOS targets and XcodeGen. Upstream StikPair is pinned to commit `d9661c505130a7b710225fb8ed61128527b46c7e`.

## Important limitations
- This is a **real compile pipeline**, not a tested solution for LiveContainer.
- An IPA generated here **does not guarantee** that LiveContainer 3.8.0 can keep RemotePairing alive while Settings is open, that Bonjour advertising works, or that a valid SideStore pairing record will be created.
- A PIN is shown **only when** the real Rust callback provides it; no mock or guessed PINs or pairing files.
- Do not upload any personal `.rppairing`, `.plist` containing keys, developer `.p12` certificate, provisioning profile, device secrets or credentials to this **public** repository.
- The IPA is unsigned. Test by importing it into LiveContainer; do **not** delete SideStore or replace an existing working app.

## Source and license
Engine and iOS Swift app: [StikPair](https://github.com/StikDebug/StikPair). Please respect its license: **non-commercial use**. The build packages the upstream LICENSE.
