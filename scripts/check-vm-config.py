#!/usr/bin/env python3
"""Fail if defconfig dropped essential VM/application selections."""
from pathlib import Path
import sys
lines=set(Path(sys.argv[1]).read_text().splitlines())
profile=sys.argv[2]
sfe=sys.argv[3]=='true'
required=['TARGET_armsr','TARGET_armsr_armv8','TARGET_armsr_armv8_DEVICE_generic',
          'TARGET_ROOTFS_EXT4FS','GRUB_EFI_IMAGES','QCOW2_IMAGES','VMDK_IMAGES','PACKAGE_luci']
if profile=='full':
    required += ['PACKAGE_dnsmasq-full','PACKAGE_luci-app-turboacc','PACKAGE_luci-app-openclash',
                 'PACKAGE_luci-app-adguardhome','PACKAGE_luci-theme-argon','PACKAGE_luci-app-oaf',
                 'PACKAGE_kmod-oaf','PACKAGE_kmod-nft-fullcone','PACKAGE_luci-app-nlbwmon',
                 'PACKAGE_luci-app-quickstart','PACKAGE_luci-app-store']
    if sfe:
        required += ['PACKAGE_kmod-shortcut-fe','PACKAGE_kmod-shortcut-fe-cm','PACKAGE_kmod-fast-classifier']
missing=[key for key in required if f'CONFIG_{key}=y' not in lines]
forbidden=['TARGET_mediatek','PACKAGE_kmod-switch-rtl8373','PACKAGE_kmod-switch-rtl8373n',
           'PACKAGE_realtek-poe','PACKAGE_poemgr','PACKAGE_kmod-mt7981-firmware','PACKAGE_mt7981-wo-firmware']
unexpected=[key for key in forbidden if f'CONFIG_{key}=y' in lines]
if not sfe or profile!='full':
    unexpected += [key for key in ['PACKAGE_kmod-shortcut-fe','PACKAGE_kmod-shortcut-fe-cm','PACKAGE_kmod-fast-classifier'] if f'CONFIG_{key}=y' in lines]
if missing or unexpected:
    raise SystemExit(f'Invalid VM config: missing={missing}; unexpected={unexpected}')
print(f'VM config passed: profile={profile}, SFE={sfe and profile=="full"}')
