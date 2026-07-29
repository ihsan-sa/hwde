"""Backoff driver for the remaining EasyEDA pulls (403 rate-limit aware).

Never re-requests a part already present in the symbol lib (LEARNINGS 2026-07-28
[easyeda2kicad][parts] (a): re-pulling a name with spaces/'/' duplicates the block).
"""
import re
import subprocess
import sys
import time
from pathlib import Path

BASE = Path("boards/lumina-carrier/lib/aiee")
SYM = BASE.with_suffix(".kicad_sym")
PRETTY = Path(str(BASE) + ".pretty")
LOG = Path("boards/lumina-carrier/work/pull_rest.log")

REST = ["C19229", "C116592", "C325964", "C1849461", "C25810", "C4328", "C17514",
        "C22984", "C22965", "C107038", "C149504", "C4216", "C380359", "C2297",
        "C2286", "C2913198", "C7430362", "C720477", "C15849", "C7430403",
        "C7430408", "C25804", "C23162", "C21190", "C2687129", "C83836", "C14663"]


def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def fp_names():
    return {p.name for p in PRETTY.glob("*.kicad_mod")}


def sym_count():
    t = SYM.read_text(encoding="utf-8", errors="replace")
    return len(re.findall(r'\n  \(symbol "', t))


def pull(lcsc):
    cp = subprocess.run([sys.executable, "-m", "easyeda2kicad",
                         f"--lcsc_id={lcsc}", "--output", str(BASE), "--full"],
                        capture_output=True, text=True, encoding="utf-8",
                        errors="replace", timeout=180)
    out = (cp.stdout or "") + (cp.stderr or "")
    if "403" in out or "Failed to fetch data" in out:
        return "ratelimit", out
    if "Created Kicad symbol" in out or "already exists" in out:
        return "ok", out
    return "unknown", out


def main():
    initial = int(sys.argv[1]) if len(sys.argv) > 1 else 240
    log(f"cooldown {initial}s before starting; {len(REST)} parts left")
    time.sleep(initial)
    pending = list(REST)
    backoff = 120
    round_no = 0
    while pending and round_no < 12:
        round_no += 1
        log(f"--- round {round_no}: {len(pending)} pending, syms={sym_count()}, "
            f"fps={len(fp_names())}")
        still = []
        for lcsc in pending:
            before = sym_count()
            try:
                status, out = pull(lcsc)
            except subprocess.TimeoutExpired:
                status, out = "ratelimit", "timeout"
            after = sym_count()
            if status == "ok" and after > before:
                log(f"  {lcsc} OK (syms {before}->{after})")
                time.sleep(4)
                continue
            if status == "ok":
                log(f"  {lcsc} OK-nochange (already present)")
                time.sleep(4)
                continue
            still.append(lcsc)
            log(f"  {lcsc} {status}: {out.strip().splitlines()[0][:120] if out.strip() else 'no output'}")
            if status == "ratelimit":
                log(f"  -> rate limited, sleeping {backoff}s and restarting round")
                time.sleep(backoff)
                backoff = min(backoff * 2, 900)
                # remaining parts of this round go back on the queue in order
                idx = pending.index(lcsc)
                still = still[:-1] + pending[idx:]
                break
            time.sleep(4)
        pending = still
    log(f"DONE pending={pending} syms={sym_count()} fps={len(fp_names())}")


if __name__ == "__main__":
    main()
