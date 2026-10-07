#!/usr/bin/env bash
set -euo pipefail
# Usage: bash run-vm-macos.sh path/to/ext4-combined-efi.img.gz
# Uses a separate writable copy. Host forwards bind to localhost only.
IMAGE=${1:?Usage: bash run-vm-macos.sh path/to/ext4-combined-efi.img.gz}
command -v qemu-system-aarch64 >/dev/null || { echo 'Install QEMU: brew install qemu'; exit 1; }
if [[ $(uname -s) != Darwin || $(uname -m) != arm64 ]]; then
  echo 'This launcher requires an Apple Silicon Mac.'; exit 1
fi
DIR=$(cd "$(dirname "$IMAGE")" && pwd)
IMAGE="$DIR/$(basename "$IMAGE")"
DISK="$DIR/vm-working.img"
if [[ ! -e "$DISK" ]]; then
  case "$IMAGE" in
    *.img.gz) python3 "$(dirname "$0")/unpack-vm-image.py" "$IMAGE" "$DISK.tmp" ;;
    *.img) cp "$IMAGE" "$DISK.tmp" ;;
    *) echo 'Use the ext4 combined EFI .img.gz or .img image.'; exit 1 ;;
  esac
  mv "$DISK.tmp" "$DISK"
fi
BREW_PREFIX=$(brew --prefix qemu)
EFI=${VM_EFI:-"$BREW_PREFIX/share/qemu/edk2-aarch64-code.fd"}
[[ -f "$EFI" ]] || { echo "EFI firmware missing: $EFI"; exit 1; }
echo 'LuCI: http://127.0.0.1:8080  SSH: ssh -p 2222 root@127.0.0.1'
echo 'First login: root, no password; set a password after logging in.'
echo 'QEMU serial exit: Ctrl-A, X. Persistent disk: '"$DISK"
exec qemu-system-aarch64 \
  -machine virt -accel hvf -cpu host -smp 2 -m 1024 \
  -bios "$EFI" -nographic \
  -drive "file=$DISK,format=raw,if=virtio" \
  -netdev 'user,id=lan,net=192.168.88.0/24,host=192.168.88.2,dhcpstart=192.168.88.100,restrict=on,hostfwd=tcp:127.0.0.1:8080-192.168.88.1:80,hostfwd=tcp:127.0.0.1:2222-192.168.88.1:22' \
  -device virtio-net-pci,netdev=lan,mac=52:54:00:88:00:01 \
  -netdev user,id=wan,net=10.0.2.0/24 \
  -device virtio-net-pci,netdev=wan,mac=52:54:00:88:00:02
