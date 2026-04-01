#!/usr/bin/env python3
"""
patch-ttyd-menu.py
------------------
将 luci-app-ttyd 子页面的菜单路径从「system」改到「services」。

通过设备实际文件确认 (ImmortalWrt 24.10.1 / LuCI 25.x)：
  /usr/share/luci/menu.d/luci-app-ttyd.json 实际内容：

    "admin/services/ttyd"        ← 顶级入口，上游已正确，不改
    "admin/system/ttyd/ttyd"     ← 需要改为 admin/services/ttyd/ttyd
    "admin/system/ttyd/config"   ← 需要改为 admin/services/ttyd/config

此脚本由 build-seed-ac2.yml Step 6b Patch E 调用。
"""

import sys, os, json, glob


def patch_json_menu(path):
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    original = raw

    # 精确替换两个子页面 key（含层级前缀，不会误伤顶级入口）
    raw = raw.replace('"admin/system/ttyd/ttyd"',   '"admin/services/ttyd/ttyd"')
    raw = raw.replace('"admin/system/ttyd/config"', '"admin/services/ttyd/config"')

    # 兜底：如果顶级入口也是 system（老版本/未来回退），且没有 services 版
    if '"admin/system/ttyd"' in raw and '"admin/services/ttyd"' not in raw:
        raw = raw.replace('"admin/system/ttyd"', '"admin/services/ttyd"')

    if raw == original:
        try:
            data = json.loads(raw)
            keys = [k for k in data if "ttyd" in k]
            print(f"  [json] no changes needed, current keys: {keys}")
        except Exception:
            print(f"  [json] no changes needed: {path}")
        return False

    # 验证 JSON 仍然合法
    try:
        data = json.loads(raw)
        keys = [k for k in data if "ttyd" in k]
        print(f"  [json] patched, new keys: {keys}")
    except json.JSONDecodeError as e:
        print(f"  [json] ERROR: broken JSON after patch: {e} — rolling back")
        return False

    with open(path, "w", encoding="utf-8") as f:
        f.write(raw)
    print(f"  [json] written: {path}")
    return True


def patch_lua_controller(path):
    with open(path, "r", encoding="utf-8") as f:
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


def patch_ttyd_dir(ttyd_dir):
    print(f"Patching ttyd menu in: {ttyd_dir}")
    patched_any = False

    for jf in glob.glob(os.path.join(ttyd_dir, "**", "menu.d", "*.json"), recursive=True):
        if patch_json_menu(jf):
            patched_any = True

    for lf in glob.glob(os.path.join(ttyd_dir, "**", "*.lua"), recursive=True):
        if patch_lua_controller(lf):
            patched_any = True

    print(f"  {'✓ patched' if patched_any else '⚠ nothing to patch'} in {ttyd_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: patch-ttyd-menu.py <ttyd_luci_dir>")
        sys.exit(1)
    ttyd_dir = sys.argv[1]
    if not os.path.isdir(ttyd_dir):
        print(f"ERROR: directory not found: {ttyd_dir}")
        sys.exit(1)
    patch_ttyd_dir(ttyd_dir)
