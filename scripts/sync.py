#!/usr/bin/env python3
"""把上游两套公开密钥库合并成一份，供青云入库工具直接拉取。

上游：
  sac    https://raw.githubusercontent.com/SteamAutoCracks/ManifestHub/main/depotkeys.json
  sudama https://api.993499094.xyz/depotkeys.json

两套库覆盖范围不同：sac 老游戏全，sudama 新上架游戏更新快。
合并规则：同一个 depot 优先保留非空值，先到先得（两套库同 key 时值一致）。
"""
import json
import os
import sys
import time
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

SOURCES = [
    ("sac", "https://raw.githubusercontent.com/SteamAutoCracks/ManifestHub/main/depotkeys.json"),
    ("sudama", "https://api.993499094.xyz/depotkeys.json"),
]

MIRRORS = [
    "{url}",
    "https://ghfast.top/{url}",
    "https://gh-proxy.com/{url}",
    "https://ghproxy.net/{url}",
]

OUT_DIR = "out"
TIMEOUT = 600


def fetch(url):
    for m in MIRRORS:
        u = m.format(url=url)
        try:
            req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                raw = r.read()
            data = json.loads(raw.decode("utf-8"))
            if isinstance(data, dict) and data:
                print("  ok %s -> %d entries (%.1f MB)" % (u, len(data), len(raw) / 1048576))
                return data
        except Exception as e:
            print("  fail %s: %s" % (u, e), file=sys.stderr)
    return None


def main():
    merged = {}
    stats = {}
    for name, url in SOURCES:
        print("[%s] %s" % (name, url))
        data = fetch(url)
        if not data:
            stats[name] = {"ok": False, "entries": 0}
            continue
        non_empty = 0
        for k, v in data.items():
            if not v:
                continue
            non_empty += 1
            if not merged.get(k):
                merged[k] = v
        stats[name] = {"ok": True, "entries": len(data), "non_empty": non_empty}

    if not merged:
        print("all sources failed, abort", file=sys.stderr)
        return 1

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "depotkeys.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, separators=(",", ":"), ensure_ascii=False)

    meta = {
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "entries": len(merged),
        "bytes": os.path.getsize(out_path),
        "sources": stats,
    }
    with open(os.path.join(OUT_DIR, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print("merged: %d entries, %.1f MB" % (len(merged), meta["bytes"] / 1048576))
    return 0


if __name__ == "__main__":
    sys.exit(main())
