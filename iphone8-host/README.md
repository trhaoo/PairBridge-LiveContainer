# StikPairHost for iPhone 8 jailbreak (iOS 16)

This is an experimental **ad-hoc signed** iOS 16 ARM64 command-line binary. It is not an IPA. The build embeds Info.plist and includes its copy in the ZIP. It runs natively on a jailbroken iPhone 8 rather than inside LiveContainer.

## Install for Dopamine rootless

1. Download the newest **successful** artifact `StikPairHost-iPhone8-signed-iOS16-arm64` from this repository's GitHub Actions. Unzip `StikPairHost-iPhone8.zip` in Files/Filza on iPhone 8.
2. Using Filza or NewTerm, place **StikPairHost-iPhone8** in `/var/jb/usr/local/bin/`, not `/var/mobile/`. The mobile data volume may disallow executing new binaries. Do not alter system files or remove jailbreak components.
3. If using NewTerm, with the downloaded binary already in `/var/mobile/`, execute:
   ```sh
   sudo mkdir -p /var/jb/usr/local/bin
   sudo cp /var/mobile/StikPairHost-iPhone8 /var/jb/usr/local/bin/StikPairHost-iPhone8
   sudo chmod 755 /var/jb/usr/local/bin/StikPairHost-iPhone8
   cd /var/mobile
   /var/jb/usr/local/bin/StikPairHost-iPhone8
   ```
   If `sudo` is unavailable, use Filza in its jailbreak-supported rootless mode to copy the file. You do **not** need `ldid -S` for this revised build; GitHub's macOS signing verification runs before publishing. The jailbreak must still trust its signature to execute it.
4. Keep NewTerm foreground and both devices on the same normal Wi-Fi (not guest Wi-Fi).
5. iOS 27 iPhone: Settings > Privacy & Security > Developer Mode, find **Pair with StikPair-iPhone8** or the pairing entry under Developer > Paired Macs, if shown. The exact menu may differ.
6. When a **real** PIN is printed in iPhone8's NewTerm, enter it on the iOS 27 iPhone. On success the file `/var/mobile/rp_pairing_file.plist` is created.
7. Transfer the private pairing file securely to SideStore. Never post the pairing file or its private keys publicly.

## Diagnose

- `zsh: permission denied` while executing from `/var/mobile`: use `/var/jb/usr/local/bin`, inspect `ls -l` and `mount` rather than repeatedly running `chmod`.
- `ldid: Could not find Info.plist`: use the new signed artifact; it includes an embedded plist and a copy in the ZIP.
- `killed: 9` or `operation not permitted`: the jailbroken device may reject the ad-hoc signature; report the entire error rather than changing system protections.
- `Bonjour PUBLISH FAILED`: check local Wi-Fi, potential Bonjour restrictions of command-line processes.
- A TCP handshake test is *not* a real remote pairing session.

The build success alone does not establish functional pairing on the user's devices.