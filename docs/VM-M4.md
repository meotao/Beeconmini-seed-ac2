# Mac mini M4：ImmortalWrt ARM64 虚拟机操作流程

本方案使用 BeeconMini/immortalwrt 的既有 armsr/armv8/generic EFI target。
固定主源码提交：9d076a14becd3ba8301f9290ca69abd4049776d7。
AC2 的 sysupgrade.bin 不能作为虚拟机磁盘；不要将 VM 镜像刷入 AC2。

## 1. 构建

进入仓库 Actions，选择 **Build ARM64 VM**。
工作流合入默认分支后，点击 Run workflow：

- profile=baseline：基础 LuCI、EFI、ext4、双 VirtIO 网卡，先验证启动。
- profile=full：迁移 AC2 的通用应用及 TurboACC/OAF 补丁。
- enable_sfe=false：默认关闭 SFE；仅 full 模式可选 true。

独立分支 codex/armsr-vm 上的推送自动运行 baseline。
基础构建成功后再运行 full。full 外部应用源仍随分支更新，需检查最终配置。
工作流使用 Ubuntu 22.04，从源码编译；一次运行最长 6 小时。

## 2. 下载与验证

打开成功的运行记录，下载 **ImmortalWrt-ARM64-VM-<profile>-<run>** Artifact。
只有镜像生成且 QEMU EFI 启动、LuCI HTTP、两张网卡及 WAN DHCP 检查通过后才上传这个 Artifact。
失败时下载 ARM64-VM-diagnostics，检查 build.log、final config、serial.log。
此工作流不自动创建 Release。

解压 Artifact，在该目录运行：

~~~sh
shasum -a 256 -c SHA256SUMS
~~~

主镜像为 *-armsr-armv8-generic-ext4-combined-efi.img.gz。
同时提供 qcow2、vmdk；这些格式并不保证 Fusion/Parallels 启动兼容。
final.config、source.commit、feeds.buildinfo.vm 记录实际构建配置与 feeds。
smoke-result.json 和 serial.log 记录 CI 的启动验证结果。
CI 使用 x86 Linux 主机上的 QEMU TCG；M4 HVF 需本机另行验证。

## 3. 在 M4 使用 QEMU 启动

~~~sh
brew install qemu
bash run-vm-macos.sh ./immortalwrt-armsr-armv8-generic-ext4-combined-efi.img.gz
~~~

如果实际文件名前缀不同，使用下载目录里的完整 .img.gz 文件名。
脚本解压生成独立可写的 vm-working.img，重启会保留配置。
默认 2 vCPU、1GB RAM、HVF 加速、EFI 固件、两张 VirtIO 网卡。

- LuCI：http://127.0.0.1:8080
- SSH：ssh -p 2222 root@127.0.0.1
- 首次账户：root，无密码；登录后设置密码。
- 串口退出：Ctrl-A，再按 X。正常关机可在 guest 执行 poweroff。
- EFI 固件默认取 Homebrew QEMU 的 edk2-aarch64-code.fd；可通过 VM_EFI 指定路径。

## 4. 网络拓扑

~~~text
Mac localhost:8080/2222 → QEMU LAN → eth0 192.168.88.1/24
Guest WAN eth1 → QEMU DHCP/NAT 10.0.2.0/24 → Mac 网络
~~~

LAN/WAN 分别使用 MAC 52:54:00:88:00:01 和 52:54:00:88:00:02。
不连接物理网桥；主机端口仅绑定 127.0.0.1。
这里验证的是虚拟机服务与接口；要验证完整 LAN 客户端转发，应另加一个测试 guest 或网络 namespace。

## 5. 本机自动验证

在源码仓库中运行：

~~~sh
python3 scripts/smoke-vm.py /absolute/path/to/unpacked-artifact --accel hvf --timeout 300
~~~

它使用临时磁盘，验证 EFI 启动、LuCI HTTP、eth0/eth1、WAN DHCP。
输出 serial.log、smoke-result.json，检查结束后关闭测试 VM。
成功不等于 OpenClash/OAF/SFE 功能全部验证；这些需要加载测试规则并产生真实流量。

## 6. UTM 操作

创建 QEMU 后端的 ARM64 虚拟机，machine=virt，启用 UEFI，内存 1GB、2核。
导入解压后的 ext4 combined EFI raw 磁盘，磁盘使用 VirtIO。
添加两张 VirtIO 网卡，确认第一张 eth0 为 LAN，第二张 eth1 为 WAN。
WAN 可用 Shared Network。LAN 使用独立虚拟网络/相应端口映射；若软件界面不能配置相同的静态 LAN 子网，先用 QEMU 启动脚本。
不能仅给一个 DHCP 网卡就假设可以访问静态 LAN 192.168.88.1。

## 7. 其他平台及实机限制

Fusion：新建 ARM64 EFI guest，尝试 vmdk；需核实磁盘控制器和网卡驱动。
Parallels：ARM64 EFI guest 与磁盘转换/导入需另测，不承诺现成镜像直接可用。
Apple Virtualization.framework：可以配置 ARM64 EFI + raw 磁盘 + VirtIO 设备；需宿主应用。

VM 可测试界面、DNS、代理、软件防火墙和服务。无法验证 MT7981 PPE、RTL8373、RTL8221B、PoE、GPIO/MDIO/I2C、AC2 bootloader、eMMC 刷机或九口物理性能。
VM 不使用 AC2 的固定 kernel vermagic；内核模块必须匹配当前 VM 构建。
