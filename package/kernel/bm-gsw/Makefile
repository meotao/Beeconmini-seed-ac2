include $(TOPDIR)/rules.mk
include $(INCLUDE_DIR)/kernel.mk

PKG_NAME:=bm-gsw
PKG_RELEASE:=1
PKG_LICENSE:=GPL-2.0

include $(INCLUDE_DIR)/package.mk

define KernelPackage/bm-gsw
  SECTION:=kernel
  CATEGORY:=Kernel modules
  SUBMENU:=Network Devices
  TITLE:=BeeconMini GSW MDIO bridge
  FILES:=$(PKG_BUILD_DIR)/bm-gsw.ko
endef

include $(INCLUDE_DIR)/kernel-defaults.mk

define Build/Compile
endef

$(eval $(call KernelPackage,bm-gsw))
