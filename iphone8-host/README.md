# StikPairHost for iPhone 8 jailbreak (iOS 16)

This is an experimental standalone arm64 command-line host. It runs outside LiveContainer on a jailbroken iPhone 8 while the iOS 27 iPhone connects to it.

## Install

1. Connect iPhone 8 and iOS 27 iPhone to the same Wi-Fi (no Guest Wi-Fi isolation).
2. Download the successful artifact "StikPairHost-iPhone8-iOS16-arm64" from GitHub Actions. Unzip it in Files on the iPhone 8.
3. Use Filza to move "StikPairHost-iPhone8" into /var/mobile/StikPairHost-iPhone8, or into a directory NewTerm 3 can read.
4. On iPhone 8 NewTerm 3:
   cd /var/mobile
   chmod 755 StikPairHost-iPhone8
   command -v ldid
   ldid -S StikPairHost-iPhone8
   ./StikPairHost-iPhone8
5. Keep NewTerm in the foreground and the iPhone 8 awake.
6. On the iOS 27 iPhone: Settings > Privacy & Security > Developer Mode > Pair with StikPair-iPhone8. Alternatively check Settings > Developer > Paired Macs > Other Devices.
7. Enter the REAL six-digit PIN printed on iPhone 8 NewTerm. On success the terminal writes "rp_pairing_file.plist" into its working directory.
8. Transfer the private pairing file securely (AirDrop, Filza, Files) and import into SideStore.

If "ldid" is unavailable, use the jailbreak package manager to install ldid. If a binary is killed by iOS immediately, its signature/trust state may need jailbreak-specific attention. Do not disable security protections on the main iPhone.

Keep pairing files and PINs private. Never upload pairing records into the public repository. A bare TCP connection is NOT a complete RemotePairing handshake.

The binary is not signed for standard iOS installation. It is NOT an IPA. Experimental until tested on a real iPhone 8 with the chosen jailbreak.
