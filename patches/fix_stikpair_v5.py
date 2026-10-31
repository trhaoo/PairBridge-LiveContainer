#!/usr/bin/env python3
"""StikPair v5: preserve silent audio after BG task expiration, log actual TCP accept."""
from pathlib import Path

swift_path = Path("upstream/App/PairingController.swift")
s = swift_path.read_text()
old = '''                task.expirationHandler = { [weak self] in
                    guard let self = self else { return }
                    self.record("BG processing expired; listener may still be alive but iOS can suspend guest execution")
                    self.keepAlive.stopAll()
                    self.finishTask(success: false)
                    if self.isRunning {
                        self.phase = .failed("Background time expired before pairing completed.")
                    }
                }'''
new = '''                task.expirationHandler = { [weak self] in
                    guard let self = self else { return }
                    self.record("BG processing expired; preserving TCP listener and silent audio")
                    self.finishTask(success: false)
                }'''
assert old in s, "v4 first BG expiration patch target not found"
s = s.replace(old,new,1)

old2 = '''        task?.expirationHandler = { [weak self] in
            guard let self else { return }
            self.keepAlive.stopAll()
            self.finishTask(success: false)
            if self.isRunning {
                self.phase = .failed("Background time expired before a device connected. Tap Pair to try again.")
            }
        }'''
new2 = '''        task?.expirationHandler = { [weak self] in
            guard let self else { return }
            self.record("BG task expired; retaining silent audio and TCP listener")
            self.finishTask(success: false)
        }'''
assert old2 in s, "v4 second BG expiration patch target not found"
s=s.replace(old2,new2,1)

old3 = '''    let id = String(cString: serviceID)

    var txt: [String: Data] = [:]'''
new3 = '''    let id = String(cString: serviceID)
    if id == "__stikpair_tcp_accepted__" {
        DispatchQueue.main.async {
            controller.record("REAL TCP CONNECTION ACCEPTED by Rust listener on port \\(port)")
        }
        return
    }

    var txt: [String: Data] = [:]'''
assert old3 in s, "v4 readyCallback patch target not found"
s=s.replace(old3,new3,1)
swift_path.write_text(s)

rust_path = Path("upstream/rust/src/lib.rs")
rust = rust_path.read_text()
old4 = '''    let (stream, _peer) = listener
        .accept()
        .await
        .map_err(|e| format!("accept failed: {e}"))?;

    let socket = RpPairingSocket::new_device(stream);'''
new4 = '''    let (stream, _peer) = listener
        .accept()
        .await
        .map_err(|e| format!("accept failed: {e}"))?;

    emit_tcp_accepted(&cbs, port);
    let socket = RpPairingSocket::new_device(stream);'''
assert old4 in rust, "rust TCP accept patch target not found"
rust=rust.replace(old4,new4,1)
needle='''fn emit_ready(cbs: &Callbacks, service_id: &str, port: u16, host_info: &PairableHostInfo) {'''
assert needle in rust
rust=rust.replace(needle,'''// Reuse the existing ready callback only for diagnostic events.
 // Marker is never advertised as a Bonjour service; the Swift callback intercepts it.
fn emit_tcp_accepted(cbs: &Callbacks, port: u16) {
    let Some(cb) = cbs.ready else { return };
    let marker = CString::new("__stikpair_tcp_accepted__").unwrap();
    cb(cbs.ctx, marker.as_ptr(), port, ptr::null(), ptr::null(), 0);
}

'''+needle,1)
rust_path.write_text(rust)
print("StikPair v5 patch successful: TCP accept event, preserve listener/audio on BG expiry")
