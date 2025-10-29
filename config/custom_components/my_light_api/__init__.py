from __future__ import annotations

from homeassistant.core import HomeAssistant

DOMAIN = "my_light_api"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """设置 my_light_api 组件。"""
    return True
