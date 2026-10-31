#!/usr/bin/env python3
"""Instrument actual TCP connections in the genuine StikPair Rust engine.
No changes to pairing keys, PIN generation, or encrypted handshake.
"""
from pathlib import Path
p=Path("upstream/rust/src/lib.rs")
s=p.read_text()
old='''    let (stream, _peer) = listener
        .accept()
        .await
        .map_err(|e| format!("accept failed: {e}"))?;

    let socket = RpPairingSocket::new_device(stream);'''
new='''    let (stream, _peer) = listener
        .accept()
        .await
        .map_err(|e| format!("accept failed: {e}"))?;

    // Distinct diagnostic event. Intercepted by the ObjC ready callback;
    // the marker is NOT sent over Bonjour and is NOT a pairing credential.
    if let Some(cb) = cbs.ready {
        let marker = CString::new("__stikpair_tcp_accepted__").unwrap();
        cb(cbs.ctx, marker.as_ptr(), port, ptr::null(), ptr::null(), 0);
    }

    let socket = RpPairingSocket::new_device(stream);'''
assert old in s, "Pinned StikPair source changed unexpectedly"
s=s.replace(old,new,1)
p.write_text(s)
print("iPhone8 v2: Rust TCP accept event instrumented successfully")
