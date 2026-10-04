"""egress - the e2e sandbox's only way out: an allowlist CONNECT proxy.

The sandbox runs with --unshare-net, so it has a loopback and nothing else.
Two halves, stdlib only:

  serve(sock)  OUTSIDE the sandbox, a thread of the driver: an HTTP CONNECT
               proxy listening on a unix socket. It opens a tunnel only to
               port 443 of an allowed host (ALLOW) and answers 403 to every
               other request, so it never reaches 127.0.0.1, the LAN or an
               arbitrary host. Model-written code cannot reconfigure it: it
               lives in the driver's process, outside the sandbox's pid and
               mount namespaces.
  forward      INSIDE the sandbox: `egress.py forward --port P --sock S --
               CMD...` listens on 127.0.0.1:P, pipes each connection to the
               bound unix socket, runs CMD and exits with its code. claude and
               the hwde scripts reach it through HTTPS_PROXY.

It fails closed. If the proxy thread or the forwarder dies, a connection
finds nothing to talk to and fails; the sandbox has no other route, so
there is no fallback to an open network. Killing or replacing the forwarder
from inside gains nothing, because the socket behind it is still the proxy.
"""
from __future__ import annotations

import argparse
import contextlib
import socket
import socketserver
import subprocess
import sys
import threading

# api.anthropic.com for the model and platform.claude.com for its OAuth token
# refresh (login mode); the parts catalogues the skill reads: JLCPCB
# (search, DFM, cart), LCSC (datasheets) and EasyEDA (symbols and
# footprints, through easyeda2kicad). A suffix entry admits its subdomains.
ALLOW = {"api.anthropic.com", "platform.claude.com", "jlcpcb.com",
         "jlcdfm.com", "lcsc.com", "easyeda.com"}
ALLOW_SUFFIX = (".jlcpcb.com", ".lcsc.com", ".easyeda.com")
PORT = 443
MAX_HEAD = 8192


def allowed(host: str, port: int) -> bool:
    host = host.lower().rstrip(".")
    return port == PORT and (host in ALLOW or host.endswith(ALLOW_SUFFIX))


def _pipe(a: socket.socket, b: socket.socket) -> None:
    """Copy both ways until either side closes."""
    def one(src, dst):
        try:
            while True:
                buf = src.recv(65536)
                if not buf:
                    break
                dst.sendall(buf)
        except OSError:
            pass
        for s in (src, dst):
            with contextlib.suppress(OSError):
                s.shutdown(socket.SHUT_RDWR)
    t = threading.Thread(target=one, args=(b, a), daemon=True)
    t.start()
    one(a, b)
    t.join()


def _target(head: bytes) -> tuple[str, int] | None:
    """(host, port) of a well-formed CONNECT request line, else None."""
    try:
        line = head.split(b"\r\n", 1)[0].decode("ascii")
        method, authority, _ = line.split(" ", 2)
        host, port = authority.rsplit(":", 1)
        if method != "CONNECT" or not host or host.startswith("["):
            return None
        return host, int(port)
    except ValueError:
        return None


class _Handler(socketserver.BaseRequestHandler):
    def handle(self):
        c = self.request
        c.settimeout(30)
        head = b""
        try:
            while b"\r\n\r\n" not in head and len(head) < MAX_HEAD:
                buf = c.recv(4096)
                if not buf:
                    return
                head += buf
        except OSError:
            return
        tgt = _target(head)
        if tgt is None or not allowed(*tgt):
            with contextlib.suppress(OSError):
                c.sendall(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0"
                          b"\r\nConnection: close\r\n\r\n")
            return
        try:
            up = socket.create_connection(tgt, timeout=30)
        except OSError:
            with contextlib.suppress(OSError):
                c.sendall(b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0"
                          b"\r\nConnection: close\r\n\r\n")
            return
        with up:
            c.settimeout(None)
            up.settimeout(None)
            c.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
            rest = head.split(b"\r\n\r\n", 1)[1]
            if rest:
                up.sendall(rest)
            _pipe(c, up)


class _Server(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True


@contextlib.contextmanager
def serve(sock: str):
    """Run the allowlist proxy on unix socket `sock` for the with-block."""
    srv = _Server(sock, _Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        yield srv
    finally:
        srv.shutdown()
        srv.server_close()


def forward(port: int, sock: str, cmd: list[str]) -> int:
    """In-sandbox: 127.0.0.1:port -> unix sock, while cmd runs."""
    ls = socket.socket()
    ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ls.bind(("127.0.0.1", port))
    ls.listen(64)

    def conn(c):
        u = socket.socket(socket.AF_UNIX)
        try:
            u.connect(sock)
        except OSError:      # proxy gone: fail closed
            c.close()
            u.close()
            return
        with c, u:
            _pipe(c, u)

    def loop():
        while True:
            c, _ = ls.accept()
            threading.Thread(target=conn, args=(c,), daemon=True).start()
    threading.Thread(target=loop, daemon=True).start()
    return subprocess.call(cmd)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="mode", required=True)
    f = sub.add_parser("forward")
    f.add_argument("--port", type=int, required=True)
    f.add_argument("--sock", required=True)
    f.add_argument("cmd", nargs=argparse.REMAINDER)
    args = ap.parse_args(argv)
    cmd = args.cmd[1:] if args.cmd[:1] == ["--"] else args.cmd
    if not cmd:
        ap.error("forward needs a command after --")
    return forward(args.port, args.sock, cmd)


if __name__ == "__main__":
    sys.exit(main())
