from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass

from homeassistant.components import mqtt
from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.const import CONF_BRIGHTNESS, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)


CONF_STATE_TOPIC = "state_topic"
CONF_COMMAND_TOPIC = "command_topic"
CONF_BRIGHTNESS_COMMAND_TOPIC = "brightness_command_topic"
CONF_BRIGHTNESS_STATE_TOPIC = "brightness_state_topic"
CONF_BRIGHTNESS_SCALE = "brightness_scale"  # 100 for your case
CONF_UNIQUE_ID = "unique_id"


@dataclass
class Topics:
    state: str
    command: str
    brightness_command: str | None
    brightness_state: str | None


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    name = config.get(CONF_NAME, "My MQTT Light")
    state_topic: str = config[CONF_STATE_TOPIC]
    command_topic: str = config[CONF_COMMAND_TOPIC]
    brightness_cmd_topic: str | None = config.get(CONF_BRIGHTNESS_COMMAND_TOPIC)
    brightness_state_topic: str | None = config.get(CONF_BRIGHTNESS_STATE_TOPIC)
    brightness_scale: int = int(config.get(CONF_BRIGHTNESS_SCALE, 100))
    unique_id: str | None = config.get(CONF_UNIQUE_ID)

    topics = Topics(
        state=state_topic,
        command=command_topic,
        brightness_command=brightness_cmd_topic,
        brightness_state=brightness_state_topic,
    )

    async_add_entities(
        [MyMqttLight(hass, name, topics, brightness_scale=brightness_scale, unique_id=unique_id)]
    )


class MyMqttLight(LightEntity):
    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        topics: Topics,
        *,
        brightness_scale: int = 100,
        unique_id: str | None = None,
    ) -> None:
        self.hass = hass
        self._attr_name = name
        self._topics = topics
        self._brightness_scale = max(1, min(255, int(brightness_scale)))
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        self._attr_color_mode = ColorMode.BRIGHTNESS
        self._attr_is_on = False
        self._attr_brightness: int | None = None
        self._attr_unique_id = unique_id
        self._unsubs: list[callback] = []

    async def async_added_to_hass(self) -> None:
        # 订阅状态主题
        @callback
        def message_received(msg):
            payload = msg.payload.strip().upper()
            if payload in ("ON", "OFF"):
                self._attr_is_on = payload == "ON"
                self.async_write_ha_state()

        self._unsubs.append(
            await mqtt.async_subscribe(self.hass, self._topics.state, message_received, 1)
        )

        # 订阅亮度状态主题（可选）
        if self._topics.brightness_state:
            @callback
            def brightness_received(msg):
                try:
                    level = int(float(msg.payload))
                except Exception:  # noqa: BLE001
                    _LOGGER.warning("Invalid brightness payload: %s", msg.payload)
                    return
                level = max(0, min(self._brightness_scale, level))
                # 转换到 0-255
                self._attr_brightness = max(0, min(255, round(level * 255 / self._brightness_scale)))
                self.async_write_ha_state()

            self._unsubs.append(
                await mqtt.async_subscribe(self.hass, self._topics.brightness_state, brightness_received, 1)
            )

    async def async_will_remove_from_hass(self) -> None:
        for unsub in self._unsubs:
            try:
                unsub()
            except Exception:  # noqa: BLE001
                pass
        self._unsubs.clear()

    async def async_turn_on(self, **kwargs) -> None:
        # brightness_pct 优先，其次 brightness
        brightness_pct = kwargs.get("brightness_pct")
        brightness_255 = kwargs.get("brightness")

        if brightness_pct is not None:
            level = max(0, min(100, int(brightness_pct)))
        elif brightness_255 is not None:
            level = max(0, min(100, round(brightness_255 * 100 / 255)))
        else:
            level = None

        # 如果有亮度设置，直接发送亮度命令（通常会自动开灯）
        if level is not None and self._topics.brightness_command:
            await mqtt.async_publish(
                self.hass,
                self._topics.brightness_command,
                str(level if self._brightness_scale == 100 else round(level * self._brightness_scale / 100)),
                qos=1,
                retain=False,
            )
            self._attr_brightness = max(0, min(255, round(level * 255 / 100)))
            self._attr_is_on = True
        else:
            # 没有亮度设置时，只发送开灯命令
            await mqtt.async_publish(self.hass, self._topics.command, "ON", qos=1, retain=False)
            self._attr_is_on = True

        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        await mqtt.async_publish(self.hass, self._topics.command, "OFF", qos=1, retain=False)
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_update(self) -> None:
        # MQTT 模式通常通过状态主题被动更新，无需轮询
        return


