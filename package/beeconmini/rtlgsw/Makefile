include $(TOPDIR)/rules.mk

PKG_NAME:=rtlgsw
PKG_RELEASE:=1

include $(INCLUDE_DIR)/package.mk

define Package/rtlgsw
  SECTION:=utils
  CATEGORY:=Utilities
  TITLE:=BeeconMini GSW management daemon
  DEPENDS:=+libuci +libgcc +kmod-i2c-core
endef

define Package/rtlgsw/description
 BeeconMini RTL8373 management daemon. It configures the switch through
 the bm_gsw MDIO character device.
endef

define Build/Compile
endef

define Package/rtlgsw/install
	$(INSTALL_DIR) $(1)/usr/bin $(1)/etc/init.d $(1)/etc/config $(1)/etc/rc.d
	$(INSTALL_BIN) ./files/rtlgsw $(1)/usr/bin/rtlgsw
	$(INSTALL_BIN) ./files/rtlgsw.init $(1)/etc/init.d/rtlgsw
	$(INSTALL_CONF) ./files/rtlgsw.config $(1)/etc/config/rtlgsw
	ln -sf ../init.d/rtlgsw $(1)/etc/rc.d/S50rtlgsw
endef

$(eval $(call BuildPackage,rtlgsw))
