#!/usr/bin/env python3
"""Reuse AC2 application integrations, with a separate VM kernel/image/network profile."""
from pathlib import Path
import os,subprocess,sys,yaml
repo=Path(os.environ['GITHUB_WORKSPACE'])
build=Path.cwd()
profile=os.environ.get('VM_PROFILE','baseline')
sfe=os.environ.get('ENABLE_SFE','false')
def run(script):
    subprocess.run(['bash','-e','-o','pipefail','-c',script+'\n:'],check=True)
if profile=='full':
    names=['整合 TurboACC','处理 fullcone 包冲突','整合 OpenAppFilter','整合 QuickStart',
           '整合 Argon 主题','整合 AdGuard Home LuCI','更新 feeds','Patch feeds 已知 Bug','设置 Argon 为默认主题']
    source=yaml.safe_load((repo/'.github/workflows/build-seed-ac2.yml').read_text())
    steps={s['name']:s for s in source['jobs']['build']['steps']}
    for name in names:
        print(f'>>> VM package integration: {name}',flush=True)
        # Uses only these application steps: never the AC2 config, kernel ABI override or packaging.
        command=steps[name]['run']
        if name=='整合 QuickStart':
            # An optional NAS-menu search with no matches is not a build error.
            command=command.replace("xargs -r grep -L 'quickstart' | xargs -r rm -f",
                                    "xargs -r grep -L 'quickstart' | xargs -r rm -f || true")
        run(command)
else:
    run('./scripts/feeds update -a\n./scripts/feeds install -a')
# Keep one reader on the VM UART; TARGET_SERIAL also expands to ttyAMA0.
inittab=build/'target/linux/armsr/base-files/etc/inittab'
text=inittab.read_text()
placeholder='@GRUB_SERIAL@::askfirst:/usr/libexec/login.sh\n'
if text.count(placeholder)!=1:
    raise RuntimeError('Unexpected armsr inittab; refusing an unverified console edit')
inittab.write_text(text.replace(placeholder,''))
if profile=='full':
    patch=build/'target/linux/generic/hack-6.6/952-add-net-conntrack-events-support-multiple-registrant.patch'
    old='@@ -3118,8 +3126,9 @@ errout:\n \tnfnetlink_set_err(net, 0, 0, -ENOBUFS);\n \treturn 0;\n }\n #endif\n+#endif\n \n static unsigned long ctnetlink_exp_id(const struct nf_conntrack_expect *exp)\n {\n \tunsigned long id = (unsigned long)exp;\n'
    new='@@ -3139,5 +3147,6 @@ errout:\n \treturn 0;\n }\n #endif\n+#endif\n static int ctnetlink_exp_done(struct netlink_callback *cb)\n {\n'
    text=patch.read_text()
    if text.count(old)!=1:
        raise RuntimeError('TurboACC patch changed; review kernel 6.6.86 compatibility')
    patch.write_text(text.replace(old,new))
config=(repo/'configs/armsr-armv8.config').read_text()
if profile=='full': config+=(repo/'configs/vm-apps.config').read_text()
if profile=='full' and sfe=='true':
    config+='\nCONFIG_PACKAGE_luci-app-turboacc_INCLUDE_SHORTCUT_FE_CM=y\nCONFIG_PACKAGE_kmod-shortcut-fe=y\nCONFIG_PACKAGE_kmod-shortcut-fe-cm=y\nCONFIG_PACKAGE_kmod-fast-classifier=y\n'
(build/'.config').write_text(config)
run('cp -R "$GITHUB_WORKSPACE/files-vm/." package/base-files/files/\nchmod +x package/base-files/files/etc/uci-defaults/99-vm-network\nmake defconfig')
subprocess.run([sys.executable,str(repo/'scripts/check-vm-config.py'),'.config',profile,sfe],check=True)
run('git rev-parse HEAD > source.commit\n./scripts/feeds list -s > feeds.buildinfo.vm')
