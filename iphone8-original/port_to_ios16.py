#!/usr/bin/env python3
"""Faithful StikPair 1.2.0 source port to iOS 16 for iPhone 8.
Input: original StikDebug/StikPair source pinned to d9661c5.
Includes iPhone/iPad pairing, Apple TV pairing, real PR export, original assets.
Replaces iOS 27-only APIs and styles rather than editing the binary's plist.
"""
from pathlib import Path
import plistlib

root=Path("upstream")
project=root/"project.yml"
s=project.read_text()
assert 'iOS: "27.0"' in s
assert 'PRODUCT_BUNDLE_IDENTIFIER: com.stik.StikPair' in s
s=s.replace('iOS: "27.0"','iOS: "16.0"',1)
s=s.replace('PRODUCT_BUNDLE_IDENTIFIER: com.stik.StikPair','PRODUCT_BUNDLE_IDENTIFIER: org.stikpair.ios16.original',1)
s=s.replace('MARKETING_VERSION: "1.2.0"','MARKETING_VERSION: "1.2.0-ios16"',1)
project.write_text(s)

plistpath=root/"App/Info.plist"
with plistpath.open("rb") as f: info=plistlib.load(f)
info["CFBundleDisplayName"]="StikPair iOS16"
info["UIFileSharingEnabled"]=True
info["LSSupportsOpeningDocumentsInPlace"]=True
info.pop("BGTaskSchedulerPermittedIdentifiers",None)
# Keep original local-network, Bonjour, audio, and location permission declarations.
with plistpath.open("wb") as f: plistlib.dump(info,f)

app=root/"App/StikPairApp.swift"
s=app.read_text()
assert '''    init() {
        PairingController.shared.registerBackgroundTask()
    }

''' in s
s=s.replace('''    init() {
        PairingController.shared.registerBackgroundTask()
    }

''','',1)
app.write_text(s)

p=root/"App/PairingController.swift"
s=p.read_text()
def sub(old,new):
    global s
    assert old in s, "PairingController.swift expected source not found: "+old[:100]
    s=s.replace(old,new,1)

sub('import BackgroundTasks\n','import UIKit\n')
sub('final class PairingController: ObservableObject {','final class PairingController: NSObject, ObservableObject, NetServiceDelegate {')
sub('    static let taskIdentifier = (Bundle.main.bundleIdentifier ?? "com.stik.StikPair") + ".pairing"\n','')
sub('''    @Published var phase: Phase = .idle''','''    @Published var phase: Phase = .idle
    @Published private(set) var diagnosticLines: [String] = []
    fileprivate func record(_ message: String) {
        let line = "[\\(Date().formatted(date: .omitted, time: .standard))] \\(message)"
        diagnosticLines.append(line)
        if diagnosticLines.count > 80 { diagnosticLines.removeFirst() }
    }''')
sub('''    private var bgTask: BGContinuedProcessingTask?
    private var pairingStarted = false
    private var taskFinished = false''','''    private var legacyBackgroundId: UIBackgroundTaskIdentifier = .invalid
    private var pairingStarted = false''')
sub('''    private init() {
        discoverySubscription''','''    private override init() {
        super.init()
        discoverySubscription''')
start=s.index('    nonisolated func registerBackgroundTask() {')
end=s.index('    func start() {',start)
s=s[:start]+s[end:]

sub('''        phase = .waiting

        UNUserNotificationCenter''','''        phase = .waiting
        record("Pair requested on iOS 16; silent audio=\\(keepAliveAudio); location=\\(keepAliveLocation)")

        UNUserNotificationCenter''')
sub('''            guard await localNetwork.request() else {
                keepAlive.stopAll()''','''            guard await localNetwork.request() else {
                record("Local Network permission DENIED")
                keepAlive.stopAll()''')
sub('''            submitBackgroundTask()
        }
    }''','''            record("Local Network permission OK")
            submitBackgroundTask()
        }
    }''')

start=s.index('    private func submitBackgroundTask() {')
end=s.index('    private func runPairing(task: BGContinuedProcessingTask?) {',start)
s=s[:start]+'''    // BGContinuedProcessingTask requires iOS 26+. Use UIApplication's
    // background grace period on iOS 16 and optional audio/location keepalives.
    private func submitBackgroundTask() {
        if legacyBackgroundId == .invalid {
            legacyBackgroundId = UIApplication.shared.beginBackgroundTask(
                withName: "StikPair iOS16 RemotePairing"
            ) { [weak self] in
                Task { @MainActor in
                    self?.record("UIKit background grace period expired; listening may be suspended")
                    self?.endLegacyBackgroundTime()
                }
            }
            record("UIKit background task started")
        }
        runPairing()
    }

    private func endLegacyBackgroundTime() {
        let id = legacyBackgroundId
        legacyBackgroundId = .invalid
        if id != .invalid { UIApplication.shared.endBackgroundTask(id) }
    }

'''+s[end:]
start=s.index('    private func runPairing(task: BGContinuedProcessingTask?) {')
end=s.index('        let bind = bindAddress',start)
s=s[:start]+'''    private func runPairing() {
        guard !pairingStarted else { return }
        pairingStarted = true
        record("Launching genuine Rust TCP listener")
'''+s[end:]

sub('''                self.stopAdvertising()
                self.keepAlive.stopAll()''','''                self.record("Rust handshake ended, status=\\(rc), success=\\(rc == 0)")
                self.stopAdvertising()
                self.keepAlive.stopAll()''')
sub('''                    self.bgTask?.progress.completedUnitCount = 100
                    self.postReturnNotification()''','''                    self.postReturnNotification()''')
sub('''                self.finishTask(success: rc == 0)''','''                self.endLegacyBackgroundTime()''')
start=s.index('    private func finishTask(success: Bool) {')
end=s.index('    fileprivate func startAdvertising(',start)
s=s[:start]+s[end:]
sub('''        stopAdvertising()
        let service = NetService(''','''        stopAdvertising()
        record("Bonjour advertising TCP port \\(port)")
        let service = NetService(''')
sub('''        service.publish()
        netService = service''','''        service.delegate = self
        service.publish()
        record("Bonjour publish requested")
        netService = service''')
sub('''    fileprivate func presentPin(_ pin: String) {
        phase = .showPin(pin)
        bgTask?.progress.completedUnitCount = 50
        bgTask?.updateTitle("StikPair", subtitle: "Enter code \\(pin) on this device")''','''    fileprivate func presentPin(_ pin: String) {
        record("REAL PIN CALLBACK from Rust")
        phase = .showPin(pin)''')
sub('''    private func stopAdvertising() {
        netService?.stop()''','''    private func stopAdvertising() {
        netService?.delegate = nil
        netService?.stop()''')
needle='''    fileprivate func presentPin(_ pin: String) {'''
assert needle in s
s=s.replace(needle,'''    nonisolated func netServiceDidPublish(_ sender: NetService) {
        Task { @MainActor [weak self] in
            self?.record("Bonjour DID PUBLISH on port \\(sender.port)")
        }
    }

    nonisolated func netService(_ sender: NetService, didNotPublish errorDict: [String: NSNumber]) {
        let details = errorDict.description
        Task { @MainActor [weak self] in
            self?.record("Bonjour FAILED: \\(details)")
        }
    }

'''+needle,1)
sub('''    DispatchQueue.main.async {
        controller.startAdvertising(serviceID: id, port: Int32(port), txt: txt)''','''    DispatchQueue.main.async {
        controller.record("Rust READY: port=\\(port), TXT records=\\(count)")
        controller.startAdvertising(serviceID: id, port: Int32(port), txt: txt)''')
p.write_text(s)

ui=root/"App/ContentView.swift"
s=ui.read_text()
assert s.count('.buttonStyle(.glass)')>=5
s=s.replace('.buttonStyle(.glass)', '.buttonStyle(.borderedProminent)')
s=s.replace('''                .glassEffect(.regular, in: .rect(cornerRadius: 20))''',
'''                .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 20))''')
s=s.replace('''                    .glassEffect(.regular, in: .rect(cornerRadius: 16))''',
'''                    .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))''')
s=s.replace('''                    .glassEffect(.regular, in: .capsule)''',
'''                    .background(.regularMaterial, in: Capsule())''')
s=s.replace('''                    .onChange(of: appleTVPin) { _, value in''',
'''                    .onChange(of: appleTVPin) { value in''')
s=s.replace('Text("StikPair")','Text("StikPair iOS16")',1)
s=s.replace('Text("On this device:")','Text("On your main iPhone / iPad:")',1)
s=s.replace('''                Text("If **Pair with StikPair** doesn't show up, close the app and try again.")''',
'''                Text("Keep this iPhone 8 awake with StikPair open. Your main iPhone must connect to this device over Wi-Fi.")''')
s=s.replace('''                Text("Waiting for a device to connect…")
                    .foregroundStyle(.secondary)''',
'''                Text("Waiting for your main iPhone to connect…")
                    .foregroundStyle(.secondary)
                VStack(alignment: .leading, spacing: 4) {
                    Text("Diagnostics").font(.caption.bold())
                    Text(controller.diagnosticLines.suffix(6).joined(separator: "\\n"))
                        .font(.caption2.monospaced())
                        .textSelection(.enabled)
                }
                .frame(maxWidth: .infinity, alignment: .leading)''',1)
s=s.replace('Text("Enable one or more of these if the Live Activity doesn\\'t start.")',
'''Text("On iOS 16, silent audio and location may help while you open Settings on the other phone.")''')
# Newer SwiftUI default values and iOS17+ Preview macro should not be required
if '#Preview {' in s:
    s=s[:s.index('#Preview {')].rstrip()+"\n"
assert '.glassEffect(' not in s
assert '.buttonStyle(.glass)' not in s
ui.write_text(s)

# Default foreground keepalive optional and configurable, but we can recommend it.
print("StikPair original 1.2.0 -> full SwiftUI iOS16 source port: Apple TV, real PR export, Bonjour, iPhone/iPad support")
