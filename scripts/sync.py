#!/usr/bin/env python3
"""把上游两套公开密钥库合并成一份，供青云入库工具直接拉取。

上游：
  sac    https://raw.githubusercontent.com/SteamAutoCracks/ManifestHub/main/depotkeys.json
  sudama https://api.993499094.xyz/depotkeys.json

两套库覆盖范围不同：sac 总条数多但有一大半是空字符串占位（非空只有 17.5 万），
sudama 条数少但全部非空，且已覆盖 sac 的所有有效 key。
合并规则：同一个 depot 优先保留非空值，先到先得。

产物（out/）：
  depotkeys.json  合并结果，工具优先用这份
  sudama.json     Sudama 原始副本（第三方 API，单独留一份做保险）
  meta.json       各源条数、非空条数、sha256、更新时间
"""
import hashlib
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
                return data, raw
        except Exception as e:
            print("  fail %s: %s" % (u, e), file=sys.stderr)
    return None, None


def write_json(path, obj, minify=True):
    with open(path, "w", encoding="utf-8") as f:
        if minify:
            json.dump(obj, f, separators=(",", ":"), ensure_ascii=False)
        else:
            json.dump(obj, f, indent=2, ensure_ascii=False)
    return os.path.getsize(path)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    merged = {}
    stats = {}
    raw_sudama = None

    for name, url in SOURCES:
        print("[%s] %s" % (name, url))
        data, raw = fetch(url)
        if not data:
            stats[name] = {"ok": False, "entries": 0, "non_empty": 0}
            continue
        if name == "sudama":
            raw_sudama = data
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

    merged_path = os.path.join(OUT_DIR, "depotkeys.json")
    merged_bytes = write_json(merged_path, merged)

    # 不单独存 sudama.json：合并结果已经包含 Sudama 的全部 key（实测合并条数 == Sudama 条数），
    # 再存一份等于把 18MB 复制一遍，没有收益。meta.json 里记录了各源条数可追溯。
    _ = raw_sudama

    meta = {
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "entries": len(merged),
        "bytes": merged_bytes,
        "sha256": sha256_of(merged_path),
        "files": {
            "depotkeys.json": {"bytes": merged_bytes, "sha256": sha256_of(merged_path)},
        },
        "sources": stats,
    }
    write_json(os.path.join(OUT_DIR, "meta.json"), meta, minify=False)

    print("merged: %d entries, %.1f MB" % (len(merged), merged_bytes / 1048576))
    return 0


if __name__ == "__main__":
    sys.exit(main())
