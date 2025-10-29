from __future__ import annotations

from homeassistant.core import HomeAssistant

DOMAIN = "my_light_mqtt"
PLATFORMS = ["light"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """设置 my_light_mqtt 组件。"""
    return True


async def async_setup_entry(hass, entry):
    """设置配置条目。"""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)


async def async_unload_entry(hass, entry):
    """卸载配置条目。"""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


