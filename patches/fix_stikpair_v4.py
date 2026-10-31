#!/usr/bin/env python3
"""StikPair v4: add observable Bonjour publish/error and task-expiry diagnostics."""
from pathlib import Path
p=Path("upstream/App/PairingController.swift")
s=p.read_text()
needle="final class PairingController: ObservableObject {"
assert needle in s
s=s.replace(needle,"final class PairingController: NSObject, ObservableObject, NetServiceDelegate {",1)
s=s.replace("    private init() {\n        discoverySubscription", "    private override init() {\n        super.init()\n        discoverySubscription",1)
old="""        service.publish()
        record("Bonjour publish() requested; this does not prove discovery or TCP connectivity")"""
new="""        service.delegate = self
        service.publish()
        record("Bonjour publish() requested; awaiting netServiceDidPublish or didNotPublish")"""
assert old in s
s=s.replace(old,new,1)
mark="    fileprivate func presentPin(_ pin: String) {"
assert mark in s
s=s.replace(mark,'''    nonisolated func netServiceDidPublish(_ sender: NetService) {
        Task { @MainActor [weak self] in
            self?.record("Bonjour DID PUBLISH service on port \\(sender.port)")
        }
    }

    nonisolated func netService(_ sender: NetService, didNotPublish errorDict: [String: NSNumber]) {
        let failureDetails = errorDict.description
        Task { @MainActor [weak self] in
            self?.record("Bonjour PUBLISH FAILED: \\(failureDetails)")
        }
    }

'''+mark,1)
# The task's expiration must be recorded but does not prove the TCP listener has stopped.
s=s.replace('record("BG processing expired")','record("BG processing expired; listener may still be alive but iOS can suspend guest execution")',1)
p.write_text(s)
print("v4 diagnostics: Bonjour delegate publication success/failure and task expiry")
