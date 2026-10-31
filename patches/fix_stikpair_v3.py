#!/usr/bin/env python3
"""Rebuild the user's original StikPair 1.2.0 engine with pairing diagnostics.
No fabricated pairing records or PINs.
"""
from pathlib import Path
import plistlib

root = Path("upstream")
project = root / "project.yml"
src = project.read_text()
assert "com.stik.StikPair" in src
project.write_text(src.replace("com.stik.StikPair", "org.stikpair.fixv3"))

info_path = root / "App/Info.plist"
with info_path.open("rb") as f:
    info = plistlib.load(f)
info["CFBundleDisplayName"] = "StikPair Fix v3"
with info_path.open("wb") as f:
    plistlib.dump(info, f)

path = root / "App/PairingController.swift"
s = path.read_text()

def sub(old, new):
    global s
    assert old in s, "PairingController.swift structure changed: " + old[:70]
    s = s.replace(old, new, 1)

sub('UserDefaults.standard.bool(forKey: "keepAlive.audio")',
    '(UserDefaults.standard.object(forKey: "keepAlive.audio") == nil ? true : UserDefaults.standard.bool(forKey: "keepAlive.audio"))')

sub('    @Published var phase: Phase = .idle',
'''    @Published var phase: Phase = .idle
    @Published private(set) var diagnosticLines: [String] = []

    var diagnosticURL: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("StikPair-Fix-v3-diagnostics.txt")
    }

    fileprivate func record(_ message: String) {
        let stamp = ISO8601DateFormatter().string(from: Date())
        let line = "[\\(stamp)] \\(message)"
        diagnosticLines.append(line)
        if diagnosticLines.count > 40 { diagnosticLines.removeFirst() }
        guard let data = (line + "\\n").data(using: .utf8) else { return }
        let url = diagnosticURL
        if FileManager.default.fileExists(atPath: url.path) {
            if let fh = try? FileHandle(forWritingTo: url) {
                fh.seekToEndOfFile()
                fh.write(data)
                try? fh.close()
            }
        } else {
            try? data.write(to: url, options: .atomic)
        }
    }''')

sub('''        phase = .waiting

        UNUserNotificationCenter''',
'''        phase = .waiting
        record("Pair requested; bundle=\\(Bundle.main.bundleIdentifier ?? "nil"); silentAudio=\\(keepAliveAudio); location=\\(keepAliveLocation)")

        UNUserNotificationCenter''')

sub('''            guard await localNetwork.request() else {
                keepAlive.stopAll()''',
'''            guard await localNetwork.request() else {
                record("Local Network permission probe FAILED")
                keepAlive.stopAll()''')

sub('''            submitBackgroundTask()
        }
    }''',
'''            record("Local Network permission probe OK")
            submitBackgroundTask()
        }
    }''')

sub('''            try BGTaskScheduler.shared.submit(request)
            DispatchQueue.main.asyncAfter(deadline: .now() + 3) { [weak self] in
                guard let self, !self.pairingStarted else { return }
                self.runPairing(task: nil)
            }
        } catch {
            runPairing(task: nil)''',
'''            try BGTaskScheduler.shared.submit(request)
            record("BGContinuedProcessingTask submitted; starting TCP listener immediately")
            // Do not depend on a queued BG task or a three-second timer.
            runPairing(task: nil)
        } catch {
            record("BG task submission error: \\(error.localizedDescription); starting TCP listener directly")
            runPairing(task: nil)''')

sub('''        guard !pairingStarted else { return }
        pairingStarted = true
        taskFinished = false''',
'''        if pairingStarted {
            // The listener was started immediately: attach the task whenever
            // the system finally launches our BGContinuedProcessingTask.
            if let task = task {
                bgTask = task
                task.progress.totalUnitCount = 100
                task.progress.completedUnitCount = 5
                task.expirationHandler = { [weak self] in
                    guard let self = self else { return }
                    self.record("BG processing expired")
                    self.keepAlive.stopAll()
                    self.finishTask(success: false)
                    if self.isRunning {
                        self.phase = .failed("Background time expired before pairing completed.")
                    }
                }
                record("BG processing attached to active TCP listener")
            }
            return
        }
        record("Launching Rust TCP listener now")
        pairingStarted = true
        taskFinished = false''')

sub('''        let service = NetService(
            domain: "",''',
'''        record("Rust listener READY: requesting Bonjour service advertising on TCP port \\(port)")
        let service = NetService(
            domain: "",''')

sub('''        service.publish()
        netService = service''',
'''        service.publish()
        record("Bonjour publish() requested; this does not prove discovery or TCP connectivity")
        netService = service''')

sub('''    fileprivate func presentPin(_ pin: String) {
        phase = .showPin(pin)''',
'''    fileprivate func presentPin(_ pin: String) {
        record("REAL PIN CALLBACK received from Rust (PIN intentionally omitted from logs)")
        phase = .showPin(pin)''')

sub('''        if keepAliveAudio || keepAliveLocation {
            notify(id: "stikpair.pin",
                   title: "StikPair pairing code",
                   body: "Enter \\(pin) on this device to pair.")
        }''',
'''        notify(id: "stikpair.pin",
               title: "StikPair pairing code",
               body: "Enter \\(pin) on this device to pair.")''')

sub('''            DispatchQueue.main.async {
                self.stopAdvertising()''',
'''            DispatchQueue.main.async {
                self.record("Rust pairing finished; exit code=\\(rc); success=\\(rc == 0)")
                self.stopAdvertising()''')

sub('''    DispatchQueue.main.async {
        controller.startAdvertising(serviceID: id, port: Int32(port), txt: txt)''',
'''    DispatchQueue.main.async {
        controller.record("Rust READY callback; port=\\(port); TXT records=\\(count)")
        controller.startAdvertising(serviceID: id, port: Int32(port), txt: txt)''')

path.write_text(s)

ui_path = root / "App/ContentView.swift"
ui = ui_path.read_text()
needle='''                Text("Waiting for a device to connect…")
                    .foregroundStyle(.secondary)'''
assert needle in ui
ui = ui.replace(needle, '''                Text("Waiting for a device to connect…")
                    .foregroundStyle(.secondary)
                VStack(alignment: .leading, spacing: 5) {
                    Text("Pairing diagnostics (no private keys or PINs)")
                        .font(.caption.bold())
                    Text(controller.diagnosticLines.suffix(4).joined(separator: "\\n"))
                        .font(.caption2.monospaced())
                        .textSelection(.enabled)
                        .fixedSize(horizontal: false, vertical: true)
                    ShareLink(item: controller.diagnosticURL) {
                        Label("Export diagnostic log", systemImage: "square.and.arrow.up")
                            .font(.caption)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(8)''', 1)
ui_path.write_text(ui)

print("Patched StikPair v3: immediate TCP listener + background task attachment + persistent diagnostics")
