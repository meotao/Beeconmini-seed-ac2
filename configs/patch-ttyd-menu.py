#!/usr/bin/env python3
"""
patch-ttyd-menu.py
将 luci-app-ttyd 菜单从「系统」移到「服务」。

原始 luci-app-ttyd.json（来自 immortalwrt/luci 源码确认）：
  "admin/system/ttyd"        → 改为 "admin/services/ttyd"
  "admin/system/ttyd/ttyd"   → 改为 "admin/services/ttyd/ttyd"
  "admin/system/ttyd/config" → 改为 "admin/services/ttyd/config"

用法：python3 patch-ttyd-menu.py <luci-app-ttyd 目录>
"""

import sys, os, json, glob


def patch_json(path):
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    original = raw

    raw = raw.replace('"admin/system/ttyd/ttyd"',   '"admin/services/ttyd/ttyd"')
    raw = raw.replace('"admin/system/ttyd/config"', '"admin/services/ttyd/config"')
    raw = raw.replace('"admin/system/ttyd"',        '"admin/services/ttyd"')

    if raw == original:
        print(f"  [json] no changes: {path}")
        return False

    try:
        data = json.loads(raw)
        keys = [k for k in data if "ttyd" in k]
        print(f"  [json] patched keys: {keys}")
    except json.JSONDecodeError as e:
        print(f"  [json] ERROR: broken JSON after patch: {e} — skipping")
        return False

    with open(path, "w", encoding="utf-8") as f:
        f.write(raw)
    return True


def patch_lua(path):
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    original = raw
    for old, new in [
        ('entry({"admin","system","ttyd"}',   'entry({"admin","services","ttyd"}'),
        ('entry({"admin", "system", "ttyd"}', 'entry({"admin", "services", "ttyd"}'),
    ]:
        raw = raw.replace(old, new)
    if raw == original:
        return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(raw)
    print(f"  [lua] patched: {path}")
    return True


def patch_dir(d):
    print(f"Patching: {d}")
    patched = False
    for f in glob.glob(os.path.join(d, "**", "menu.d", "*.json"), recursive=True):
        if patch_json(f): patched = True
    for f in glob.glob(os.path.join(d, "**", "*.lua"), recursive=True):
        if patch_lua(f): patched = True
    print(f"  {'✓ done' if patched else '⚠ nothing matched'}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or not os.path.isdir(sys.argv[1]):
        print("Usage: patch-ttyd-menu.py <dir>"); sys.exit(1)
    patch_dir(sys.argv[1])
