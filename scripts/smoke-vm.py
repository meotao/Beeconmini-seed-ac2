#!/usr/bin/env python3
"""Boot the actual EFI disk and verify LuCI, two NICs and WAN DHCP over serial."""
from pathlib import Path
import argparse,gzip,json,os,shutil,subprocess,time,urllib.request
p=argparse.ArgumentParser()
p.add_argument('directory',type=Path)
p.add_argument('--accel',choices=['tcg','hvf'],default='tcg')
p.add_argument('--timeout',type=int,default=900)
a=p.parse_args()
a.directory=a.directory.resolve()
images=list(a.directory.glob('*-armsr-armv8-generic-ext4-combined-efi.img.gz'))
if len(images)!=1: raise SystemExit('Expected one ext4 combined EFI image')
efi=os.environ.get('VM_EFI')
if not efi:
    choices=['/usr/share/qemu-efi-aarch64/QEMU_EFI.fd','/usr/share/AAVMF/AAVMF_CODE.fd']
    if shutil.which('brew'):
        prefix=subprocess.check_output(['brew','--prefix','qemu'],text=True).strip()
        choices.insert(0,prefix+'/share/qemu/edk2-aarch64-code.fd')
    efi=next((f for f in choices if Path(f).is_file()),None)
if not efi: raise SystemExit('EFI firmware missing; set VM_EFI')
disk=a.directory/'smoke-working.img'
with gzip.open(images[0],'rb') as src,disk.open('wb') as dst: shutil.copyfileobj(src,dst)
log=a.directory/'serial.log'
cmd=['qemu-system-aarch64','-machine','virt','-accel',a.accel,'-cpu','host' if a.accel=='hvf' else 'cortex-a53',
     '-smp','2','-m','1024','-bios',efi,'-display','none','-monitor','none','-serial','stdio',
     '-drive',f'file={disk},format=raw,if=virtio,snapshot=on',
     '-netdev','user,id=lan,net=192.168.88.0/24,host=192.168.88.2,dhcpstart=192.168.88.100,restrict=on,hostfwd=tcp:127.0.0.1:18080-192.168.88.1:80',
     '-device','virtio-net-pci,netdev=lan,mac=52:54:00:88:00:01',
     '-netdev','user,id=wan,net=10.0.2.0/24',
     '-device','virtio-net-pci,netdev=wan,mac=52:54:00:88:00:02']
result={'passed':False,'image':images[0].name,'accel':a.accel}
try:
    with log.open('wb') as output:
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=output,stderr=subprocess.STDOUT)
        try:
            deadline=time.monotonic()+a.timeout
            sent=False
            last_sent=0.0
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            while time.monotonic()<deadline:
                if proc.poll() is not None: raise RuntimeError(f'QEMU exited: {proc.returncode}')
                serial=log.read_text(errors='replace')
                if time.monotonic()-last_sent > 15 and ('Please press Enter' in serial or 'procd: - init complete -' in serial):
                    proc.stdin.write(b'\n');proc.stdin.flush();time.sleep(2)
                    command=b"[ -d /sys/class/net/eth0 ] && [ -d /sys/class/net/eth1 ] && echo VM_NICS_OK; ubus call network.interface.wan status; ip -4 addr show dev eth1; ip route; echo VM_SERIAL_DONE\n"
                    proc.stdin.write(command);proc.stdin.flush();sent=True;last_sent=time.monotonic()
                if sent and 'VM_SERIAL_DONE' in serial and 'VM_NICS_OK\r\n' in serial and 'inet 10.0.2.' in serial:
                    try:
                        with opener.open('http://127.0.0.1:18080/cgi-bin/luci/',timeout=5) as response:
                            body=response.read().decode(errors='replace')
                            if response.status==200 and ('LuCI' in body or 'luci' in body or 'ImmortalWrt' in body):
                                result.update(passed=True,luci_http=response.status,two_nics=True,wan_dhcp=True)
                                break
                    except (OSError,urllib.error.URLError): pass
                time.sleep(3)
            if not result['passed']: raise RuntimeError('EFI/LuCI/two-NIC/WAN smoke test timed out; inspect serial.log')
        finally:
            proc.terminate()
            try: proc.wait(timeout=10)
            except subprocess.TimeoutExpired: proc.kill();proc.wait()
except Exception as e:
    result['error']=str(e)
finally:
    disk.unlink(missing_ok=True)
    (a.directory/'smoke-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
if not result['passed']: raise SystemExit(1)
