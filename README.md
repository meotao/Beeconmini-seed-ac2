# BeeconMini SEED AC2 固件自动构建

基于 [BeeconMini/immortalwrt](https://github.com/BeeconMini/immortalwrt)（branch `24.10.1`）为 BeeconMini SEED AC2 定制的 OpenWrt 固件自动构建仓库。

---

## 硬件规格

| 项目         | 参数                                         |
| ------------ | -------------------------------------------- |
| CPU          | MT7981B（Filogic 820，ARM Cortex-A53 ×2）    |
| 交换芯片     | RTL8373（8×2.5G，MDIO 总线）                 |
| PoE 控制器   | RTL8238B（I2C-GPIO，GPIO46/47）              |
| WAN PHY      | RTL8221B（2.5G，MDIO addr=7）                |
| 端口         | 1×WAN 2.5G + 8×LAN 2.5G PoE+（单口最大 30W） |
| 内存 / 存储  | 1G RAM + 64G eMMC                            |
| Wi-Fi        | 无                                           |
| 固件升级方式 | eMMC（`emmc_do_upgrade`）                    |

---

## 固件功能

| 功能             | 说明                                                         |
| ---------------- | ------------------------------------------------------------ |
| **PoE 管理**     | RTL8238B 控制 8 口 PoE+，单口最大 30W                        |
| **OAF 应用过滤** | [OpenAppFilter](https://github.com/destan19/OpenAppFilter)，支持抖音、王者荣耀等数百款 App 过滤 |
| **OpenClash**    | 透明代理，支持 Clash 规则                                    |
| **NLBW**         | Netlink 实时带宽监控                                         |
| **VLMCSD**       | KMS 激活服务器                                               |
| **ttyd**         | 浏览器内 Web 终端                                            |
| **iStore**       | 应用商店（第三方 feed）                                      |
| **QuickStart**   | 快速配置向导                                                 |
| **定时重启**     | 按计划自动重启                                               |
| **TurboACC**     | MTK HW NAT 硬件加速（WED offload）                           |
| **eQoS**         | MTK 带宽控制                                                 |
| **UPnP**         | miniupnpd                                                    |
| **主题**         | Argon + Bootstrap-Mod                                        |

---

## 仓库结构

```
.
├── .github/
│   └── workflows/
│       └── build-seed-ac2.yml   # 构建 workflow（仅手动触发）
├── configs/
│   ├── mt7981-common.config     # MT7981B 平台通用层（无 Wi-Fi）
│   └── seed-ac2.config          # SEED AC2 设备差异层
└── README.md
```

### 配置分层说明

```
mt7981-common.config          ← 平台层：内核选项、kmod、库、通用工具包
       +
seed-ac2.config               ← 设备层：机型声明、RTL8373 驱动、PoE、应用包
       ↓  cat 合并
     .config  →  make defconfig  →  编译
```

`seed-ac2.config` 开头声明的设备型号会覆盖平台层，`make defconfig` 自动补全其余默认值并拉入 `DEVICE_PACKAGES`（`kmod-switch-rtl8373`、`kmod-fs-f2fs`、`kmod-fs-ext4` 等）。

---

## 构建说明

### 触发构建

进入仓库 → **Actions** → `Build BeeconMini SEED AC2` → **Run workflow**

构建完成后固件自动发布为 GitHub Release，Tag 格式为 `yyyymmdd<run_number>`。

### 构建流程

```
1. 挂载 /mnt 临时盘（150 GB）
2. 检出本仓库
3. 释放 runner 磁盘空间
4. 安装编译依赖
5. git clone BeeconMini/immortalwrt (branch 24.10.1)
6. feeds update & install（含 iStore feed）
7. git clone OpenAppFilter → package/OpenAppFilter
8. cat 两层 config → .config，make defconfig
9. make download
10. make -j$(nproc)（失败自动降级为 make -j1 V=s）
11. 收集固件 → 上传 Artifact + 发布 Release
```

### 本地编译

```bash
# 克隆本仓库
git clone https://github.com/<your-name>/beeconmini-seed-ac2.git
cd beeconmini-seed-ac2

# 克隆上游源码
git clone --depth=1 -b 24.10.1 \
  https://github.com/BeeconMini/immortalwrt.git
cd immortalwrt

# 添加 iStore feed
echo "src-git istore https://github.com/linkease/istore.git;main" \
  >> feeds.conf.default

# 更新 feeds
./scripts/feeds update -a && ./scripts/feeds install -a

# 集成 OAF
git clone --depth=1 \
  https://github.com/destan19/OpenAppFilter.git \
  package/OpenAppFilter

# 合并配置
cat ../configs/mt7981-common.config \
    ../configs/seed-ac2.config \
    > .config
make defconfig

# 编译
make -j$(nproc)
```

---

## 刷机说明

| 文件               | 用途                            |
| ------------------ | ------------------------------- |
| `*sysupgrade*.bin` | 从 OpenWrt/ImmortalWrt 在线升级 |
| `*factory*.bin`    | 从原厂固件首次刷入              |

> **注意**：SEED AC2 使用 eMMC 存储，升级后配置数据保存在独立分区（`rootfs_data`），刷机不会丢失配置。

---

## 技术说明

- **subtarget**：`mediatek/filogic`（非 `mt7981`，已从上游 `Makefile` 确认 `SUBTARGETS:=filogic mt7622 mt7623 mt7629`）
- **交换架构**：DSA（`filogic/config-6.6` 中 `CONFIG_NET_DSA=y`，无 `swconfig`）
- **RTL8373 驱动**：`package/kernel/rtl8373`（`PKG_NAME:=switch-rtl8373`，依赖 `kmod-i2c-gpio`）
- **PoE 控制**：RTL8238B 通过 I2C-GPIO 桥接（DTS 节点 `i2c_rtl8238b`，`scl=GPIO46 / sda=GPIO47`）
- **OAF 集成**：clone 到 `package/` 目录（官方推荐方式），无需 feeds，`luci-app-oaf=y` 自动拉入 `kmod-oaf` + `oaf` + `luci-app-oaf`
