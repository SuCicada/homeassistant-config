from __future__ import annotations

import asyncio
import logging

import aiohttp
import async_timeout
from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.const import CONF_API_KEY, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)

CONF_LIGHT_ID = "light_id"


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    host = config[CONF_HOST]
    api_key = config.get(CONF_API_KEY)
    light_id = config[CONF_LIGHT_ID]

    async_add_entities([MyApiLight(host, light_id, api_key)])


class MyApiLight(LightEntity):
    """Representation of a light controlled via custom REST API."""

    def __init__(self, host: str, light_id: str, api_key: str | None) -> None:
        self._host = host.rstrip("/")
        self._light_id = light_id
        self._api_key = api_key
        self._attr_name = f"My API Light {self._light_id}"
        self._attr_is_on = False
        self._attr_brightness: int | None = None
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        self._attr_color_mode = ColorMode.BRIGHTNESS
        self._session: aiohttp.ClientSession | None = None

    async def async_added_to_hass(self) -> None:
        self._session = aiohttp.ClientSession()

    async def async_turn_on(self, **kwargs) -> None:
        # 支持 brightness_pct（0-100）和 brightness（0-255）
        brightness_pct: int | None = kwargs.get("brightness_pct")
        brightness_255: int | None = kwargs.get("brightness")

        if brightness_pct is not None:
            level_100 = max(0, min(100, int(brightness_pct)))
            await self._set_brightness(level_100)
            self._attr_is_on = True
            self._attr_brightness = max(0, min(255, round(level_100 * 255 / 100)))
        elif brightness_255 is not None:
            # 将 0-255 亮度转换到 0-100
            level_100 = max(0, min(100, round(brightness_255 * 100 / 255)))
            await self._set_brightness(level_100)
            # 设置亮度通常会让灯处于开状态
            self._attr_is_on = True
            self._attr_brightness = brightness_255
        else:
            await self._call_api("on")

    async def async_turn_off(self, **kwargs) -> None:
        await self._call_api("off")

    async def async_update(self) -> None:
        url = f"{self._host}/api/light/status"
        params = {"id": self._light_id}
        headers = {"Authorization": self._api_key} if self._api_key else None

        assert self._session is not None
        async with async_timeout.timeout(10):
            async with self._session.get(url, params=params, headers=headers) as resp:
                resp.raise_for_status()
                data = await resp.json()

        self._attr_is_on = data.get("is_on", False)
        # 从状态读取 0-100 的亮度并映射到 0-255
        level_100 = data.get("brightness")
        if isinstance(level_100, (int, float)):
            # 四舍五入映射到 0-255
            self._attr_brightness = max(0, min(255, round(level_100 * 255 / 100)))
        else:
            # API 未返回亮度时，保留现有亮度或设为 None
            if not self._attr_is_on:
                self._attr_brightness = None

    async def _call_api(self, action: str) -> None:
        url = f"{self._host}/api/light/{action}"
        payload = {"id": self._light_id}
        headers = {"Authorization": self._api_key} if self._api_key else None

        assert self._session is not None
        async with async_timeout.timeout(10):
            async with self._session.post(url, json=payload, headers=headers) as resp:
                if resp.status >= 400:
                    text = await resp.text()
                    _LOGGER.error("Light %s action %s failed: %s", self._light_id, action, text)
                    raise RuntimeError(f"API error {resp.status}: {text}")

        await asyncio.sleep(0)
        self.async_schedule_update_ha_state(force_refresh=True)

    async def _set_brightness(self, level_100: int) -> None:
        """调用 API 设置亮度（0-100）。"""
        url = f"{self._host}/api/light/brightness"
        payload = {"id": self._light_id, "level": int(max(0, min(100, level_100)))}
        headers = {"Authorization": self._api_key} if self._api_key else None

        assert self._session is not None
        async with async_timeout.timeout(10):
            async with self._session.post(url, json=payload, headers=headers) as resp:
                if resp.status >= 400:
                    text = await resp.text()
                    _LOGGER.error(
                        "Light %s set brightness failed: %s", self._light_id, text
                    )
                    raise RuntimeError(f"API error {resp.status}: {text}")

        await asyncio.sleep(0)
        self.async_schedule_update_ha_state(force_refresh=True)

    async def async_will_remove_from_hass(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None
