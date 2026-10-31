#!/usr/bin/env python3
"""Enable a dual-stack IPv4+IPv6 TCP listener for iOS 27 remote pairing.
Uses socket2 to explicitly disable IPV6_V6ONLY so one port accepts both
address families; falls back safely to the upstream IPv4 bind if unavailable.
"""
from pathlib import Path

cargo=Path("upstream/rust/Cargo.toml")
txt=cargo.read_text()
assert 'socket2 =' not in txt
txt=txt.replace('tokio = { version = "1", features = ["rt-multi-thread", "net", "macros", "fs"] }',
'''tokio = { version = "1", features = ["rt-multi-thread", "net", "macros", "fs"] }
socket2 = "0.6"''')
cargo.write_text(txt)

p=Path("upstream/rust/src/lib.rs")
src=p.read_text()
needle="use std::net::{IpAddr, Ipv4Addr, SocketAddr};"
assert needle in src
src=src.replace(needle,"use std::net::{IpAddr, Ipv4Addr, Ipv6Addr, SocketAddr};\nuse socket2::{Domain, Protocol, Socket, Type};",1)
old='''    let listener = TcpListener::bind(SocketAddr::new(ip, port))
        .await
        .map_err(|e| format!("failed to bind {bind_addr}:{port}: {e}"))?;
    let port = listener'''
new='''    // The advertised Bonjour host may resolve to IPv6 first.
    // Binding only 0.0.0.0 cannot accept IPv6 connections on iOS.
    // Explicitly request a dual-stack socket; keep IPv4 compatibility.
    let listener = if ip == IpAddr::V4(Ipv4Addr::UNSPECIFIED) {
        let dual_stack = (|| -> Result<TcpListener, String> {
            let sock = Socket::new(Domain::IPV6, Type::STREAM, Some(Protocol::TCP))
                .map_err(|e| format!("IPv6 socket failed: {e}"))?;
            sock.set_only_v6(false)
                .map_err(|e| format!("dual-stack option failed: {e}"))?;
            sock.bind(&SocketAddr::new(IpAddr::V6(Ipv6Addr::UNSPECIFIED), port).into())
                .map_err(|e| format!("dual-stack bind failed: {e}"))?;
            sock.listen(128)
                .map_err(|e| format!("dual-stack listen failed: {e}"))?;
            sock.set_nonblocking(true)
                .map_err(|e| format!("dual-stack nonblocking failed: {e}"))?;
            TcpListener::from_std(sock.into())
                .map_err(|e| format!("tokio dual-stack listener failed: {e}"))
        })();
        match dual_stack {
            Ok(listener) => {
                eprintln!("[Network] IPv4+IPv6 dual-stack TCP listener READY");
                listener
            }
            Err(reason) => {
                eprintln!("[Network] dual-stack unavailable ({reason}); using IPv4 fallback");
                TcpListener::bind(SocketAddr::new(ip, port))
                    .await
                    .map_err(|e| format!("failed IPv4 fallback bind: {e}"))?
            }
        }
    } else {
        TcpListener::bind(SocketAddr::new(ip, port))
            .await
            .map_err(|e| format!("failed to bind {bind_addr}:{port}: {e}"))?
    };
    let port = listener'''
assert old in src, "Pinned upstream source does not match expected listener"
src=src.replace(old,new,1)
p.write_text(src)
print("Dual-stack IPv4+IPv6 TCP listener patch applied")
