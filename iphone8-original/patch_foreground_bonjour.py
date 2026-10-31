#!/usr/bin/env python3
"""iOS 16 foreground-first / Bonjour recovery patch for original StikPair port.
Avoid overstating iOS background entitlement capabilities. The app cannot
promise indefinite background execution; keep screen awake during pairing.
"""
from pathlib import Path

p=Path("upstream/App/PairingController.swift")
s=p.read_text()
def replace_once(old,new):
    global s
    assert old in s, "Missing source anchor: "+old[:140]
    s=s.replace(old,new,1)

replace_once(
'''    private var netService: NetService?
    private let localNetwork''',
'''    private var netService: NetService?
    private var advertisedServiceID: String?
    private var advertisedPort: Int32 = 0
    private var advertisedTXT: [String: Data] = [:]
    private var bonjourPublished = false
    private var needsRefreshAfterBackground = false
    private var bonjourRetryCount = 0
    private let localNetwork''')

replace_once(
'''        super.init()
        discoverySubscription =''',
'''        super.init()
        NotificationCenter.default.addObserver(
            forName: UIApplication.didEnterBackgroundNotification,
            object: nil, queue: .main
        ) { [weak self] _ in
            Task { @MainActor in
                guard let self = self, self.pairingStarted else { return }
                self.needsRefreshAfterBackground = true
                self.record("⚠ iPhone 8 moved to BACKGROUND; iOS 16 can suspend the pairing listener")
            }
        }
        NotificationCenter.default.addObserver(
            forName: UIApplication.didBecomeActiveNotification,
            object: nil, queue: .main
        ) { [weak self] _ in
            Task { @MainActor in
                guard let self = self, self.pairingStarted else { return }
                self.record("iPhone 8 returned to FOREGROUND")
                if (self.needsRefreshAfterBackground || !self.bonjourPublished) && self.advertisedServiceID != nil {
                    self.needsRefreshAfterBackground = false
                    self.republishBonjour(reason: "returned from background")
                }
            }
        }
        discoverySubscription =''')

replace_once(
'''        phase = .waiting
        record("Pair requested on iOS 16; silent audio=\\(keepAliveAudio); location=\\(keepAliveLocation)")''',
'''        phase = .waiting
        UIApplication.shared.isIdleTimerDisabled = true
        record("Screen auto-lock disabled while pairing (keep StikPair foreground)")
        record("Pair requested on iOS 16; silent audio=\\(keepAliveAudio); location=\\(keepAliveLocation)")''')

replace_once(
'''                record("Local Network permission DENIED")
                keepAlive.stopAll()''',
'''                record("Local Network permission DENIED")
                UIApplication.shared.isIdleTimerDisabled = false
                keepAlive.stopAll()''')

replace_once(
'''                self.stopAdvertising()
                self.keepAlive.stopAll()''',
'''                self.stopAdvertising()
                UIApplication.shared.isIdleTimerDisabled = false
                self.keepAlive.stopAll()''')

replace_once(
'''    fileprivate func startAdvertising(serviceID: String, port: Int32, txt: [String: Data]) {
        stopAdvertising()
        record("Bonjour advertising TCP port \\(port)")
        let service = NetService(
            domain: "",
            type: "_remotepairing-pairable-host._tcp.",
            name: serviceID,
            port: port)
        service.setTXTRecord(NetService.data(fromTXTRecord: txt))
        service.delegate = self
        service.publish()
        record("Bonjour publish requested")
        netService = service
    }''',
'''    fileprivate func startAdvertising(serviceID: String, port: Int32, txt: [String: Data]) {
        stopAdvertising()
        advertisedServiceID = serviceID
        advertisedPort = port
        advertisedTXT = txt
        bonjourRetryCount = 0
        republishBonjour(reason: "Rust READY")
    }

    private func republishBonjour(reason: String) {
        guard pairingStarted, let serviceID = advertisedServiceID, advertisedPort > 0 else { return }
        if UIApplication.shared.applicationState == .background {
            record("Bonjour restart deferred: iPhone 8 is in background")
            return
        }
        netService?.delegate = nil
        netService?.stop()
        netService = nil
        bonjourPublished = false
        let service = NetService(
            domain: "",
            type: "_remotepairing-pairable-host._tcp.",
            name: serviceID,
            port: advertisedPort)
        service.delegate = self
        service.setTXTRecord(NetService.data(fromTXTRecord: advertisedTXT))
        netService = service
        service.publish()
        record("Bonjour publish requested · \\(reason) · TCP port \\(advertisedPort)")
    }''')

replace_once(
'''    nonisolated func netServiceDidPublish(_ sender: NetService) {
        Task { @MainActor [weak self] in
            self?.record("Bonjour DID PUBLISH on port \\(sender.port)")
        }
    }

    nonisolated func netService(_ sender: NetService, didNotPublish errorDict: [String: NSNumber]) {
        let details = errorDict.description
        Task { @MainActor [weak self] in
            self?.record("Bonjour FAILED: \\(details)")
        }
    }''',
'''    nonisolated func netServiceDidPublish(_ sender: NetService) {
        Task { @MainActor [weak self] in
            guard let self = self, self.netService === sender else { return }
            self.bonjourPublished = true
            self.bonjourRetryCount = 0
            self.record("Bonjour DID PUBLISH on port \\(sender.port)")
        }
    }

    nonisolated func netService(_ sender: NetService, didNotPublish errorDict: [String: NSNumber]) {
        let details = errorDict.description
        Task { @MainActor [weak self] in
            guard let self = self, self.netService === sender else { return }
            self.bonjourPublished = false
            self.record("Bonjour FAILED: \\(details)")
            guard self.pairingStarted, self.bonjourRetryCount < 2 else { return }
            self.bonjourRetryCount += 1
            let attempt = self.bonjourRetryCount
            self.record("Will retry Bonjour on foreground (attempt \\(attempt) of 2)")
            DispatchQueue.main.asyncAfter(deadline: .now() + 2) { [weak self] in
                guard let self = self, self.pairingStarted, !self.bonjourPublished else { return }
                self.republishBonjour(reason: "recover after publish failure")
            }
        }
    }''')

replace_once(
'''    private func stopAdvertising() {
        netService?.delegate = nil
        netService?.stop()
        netService = nil
    }''',
'''    private func stopAdvertising() {
        netService?.delegate = nil
        netService?.stop()
        netService = nil
        advertisedServiceID = nil
        advertisedPort = 0
        advertisedTXT = [:]
        bonjourPublished = false
    }''')

p.write_text(s)
ui=Path("upstream/App/ContentView.swift")
u=ui.read_text()
old='''                Text("Keep this iPhone 8 awake with StikPair open. Your main iPhone must connect to this device over Wi-Fi.")'''
assert old in u
u=u.replace(old,'''                Text("IMPORTANT: Keep StikPair OPEN on iPhone 8 with its screen ON. iOS 16 suspends ordinary background apps.")
                    .font(.caption.bold())''')
u=u.replace('''Text(controller.diagnosticLines.suffix(6).joined(separator: "\\n"))''',
'''Text(controller.diagnosticLines.suffix(8).joined(separator: "\\n"))''')
ui.write_text(u)

project=Path("upstream/project.yml")
txt=project.read_text()
assert 'CURRENT_PROJECT_VERSION: "16"' in txt
txt=txt.replace('CURRENT_PROJECT_VERSION: "16"','CURRENT_PROJECT_VERSION: "17"',1)
project.write_text(txt)
print("iOS16 foreground lock-screen prevention, lifecycle diagnostics, and bounded Bonjour retry patched")
