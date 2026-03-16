# ImmortalWrt + TurboACC 编译 (BeeconMini SEED AC2)

## 硬件规格

| 组件 | 型号 | 说明 |
|------|------|------|
| CPU | MT7981B | MediaTek Filogic |
| 交换芯片 | RTL8373 | 企业级 2.5G 网管交换芯片 (MDIO) |
| PoE 控制器 | RTL8238B | I2C-GPIO (GPIO46/47) |
| WAN PHY | RTL8221B | MDIO addr 7, SGMII |
| 端口 | 1×WAN 2.5G + 8×LAN 2.5G PoE+ | 单口最大 30W |
| 内存/存储 | 1GB + 64GB eMMC | |
| Wi-Fi | 无 | |

## 固件功能

- **TurboACC**: Flow Offload + Fullcone NAT + BBR + SFE
- **OpenClash**: 代理工具
- **OAF**: 应用过滤 (OpenAppFilter)
- **QuickStart**: iStore 快速入门
- **NLBW**: 网络带宽监控
- **vlmcsd**: KMS 激活工具
- **PoE 管理**: realtek-poe + poemgr
- **默认 LAN IP**: 192.168.88.1

## 使用方法

1. Fork 本仓库
2. 进入 Actions → "Build BeeconMini SEED AC2" → Run workflow
3. 编译完成后在 Releases 下载固件

## 配置结构

```
.github/workflows/build-seed-ac2.yml  ← 唯一 workflow
configs/mt7981-common.config           ← MT7981 平台通用配置
configs/seed-ac2.config                ← SEED AC2 设备差异配置
```

Workflow 通过 `cat` 合并两层配置后执行 `make defconfig`。

## 已知问题与经验总结

### TurboACC + SFE 集成要点

1. **必须使用官方 `add_turboacc.sh`**，不要手动拆解仓库结构。turboacc 的 package 分支使用版本化子目录 (`firewall4-<VERSION>/firewall4/`)，手动 clone 路径错误率极高。

2. **`add_turboacc.sh` 写入 `config-6.6` 的是禁用语法**：脚本写入 `# CONFIG_SHORTCUT_FE is not set` 和 `# CONFIG_NF_CONNTRACK_CHAIN_EVENTS is not set`，必须在脚本运行后手动改为 `=y`。否则 patch 953 的 `#ifdef CONFIG_SHORTCUT_FE` 不生效，`fast_forwarded` 字段不存在，SFE 编译失败。

3. **patch 953 中 `fast_forwarded` 的注入位置**：patch 953 在 `csum_not_inet:1` 行后注入 `fast_forwarded:1`，但 `csum_not_inet:1` 本身在 `#if IS_ENABLED(CONFIG_IP_SCTP)` 块内。如果 `CONFIG_IP_SCTP` 未启用，`fast_forwarded` 也被跳过。全量构建时只要 `CONFIG_SHORTCUT_FE=y` 正确设置就没问题（patch 953 有自己的 `#ifdef` 守卫），但增量编译环境需要特别注意。

4. **ImmortalWrt 自带 fullcone 支持**：ImmortalWrt 有自己的 `fullconenat-nft` 包和 firewall4/nftables/libnftnl 补丁。`add_turboacc.sh` 替换这三个包后，必须移除 `fullconenat-nft` 避免冲突。

### Kconfig 自引用 Bug

`kmod-nft-fullcone` 和 `kmod-oaf` 都有 Kconfig 自引用循环依赖 bug（`PACKAGE_kmod-xxx is selected by PACKAGE_kmod-xxx`），`make defconfig` 会静默跳过这些包。解决方案是在 `.config` 中显式声明 `=y`。

### Rust / LLVM 404

`lang/rust` 编译时从 `ci-artifacts.rust-lang.org` 下载预编译 LLVM，URL 经常 404。修复方案：`sed -i 's/download-ci-llvm=true/download-ci-llvm=false/g'`，让 LLVM 本地编译。

### libxcrypt 编译失败

libxcrypt ≤4.4.34 的 `expand-selected-hashes` 脚本在 Perl 5.34+ 上崩溃。修复：升级到 4.4.36 + 注入 `PKG_FORTIFY_SOURCE:=0`。

### OpenClash shadowsocks-rust

OpenClash 通过 Kconfig `select` 拉入 `shadowsocks-rust`，用户配置文件中的 `is not set` 无法覆盖 `select` 语义。必须在 workflow 中 `sed` 删除 Makefile 里的依赖行。

### 包名易错汇总

| 错误名称 | 正确名称 |
|----------|----------|
| `luci-app-turboacc-mtk` | `luci-app-turboacc` |
| `kmod-poe` / `poe-cli` / `luci-app-poe` | `realtek-poe` + `poemgr` |
| `nlbw` / `luci-app-nlbw` | `nlbwmon` / `luci-app-nlbwmon` |
| `kmod-rtl8373` | `kmod-switch-rtl8373` |
| `CONFIG_TARGET_mediatek_mt7981` | `CONFIG_TARGET_mediatek_filogic` |

### RTL8373 驱动版本问题

`rtl8373.ko` 是预编译二进制 (`vermagic=6.6.73`)，但 immortalwrt 24.10.1 使用 kernel 6.6.86。运行时 `insmod` 可能因版本不匹配而失败。这只能由 BeeconMini 更新 .ko 解决。

## 鸣谢

- [chenmozhijin/turboacc](https://github.com/chenmozhijin/turboacc)
- [chenmozhijin/OpenWrt-K](https://github.com/chenmozhijin/OpenWrt-K)
- [BeeconMini/immortalwrt](https://github.com/BeeconMini/immortalwrt)
- [destan19/OpenAppFilter](https://github.com/destan19/OpenAppFilter)
- [lq-wq/luci-app-quickstart](https://github.com/lq-wq/luci-app-quickstart)
- [sbwml/packages_lang_golang](https://github.com/sbwml/packages_lang_golang)
