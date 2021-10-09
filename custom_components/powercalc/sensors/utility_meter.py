from __future__ import annotations

import logging
from awesomeversion import AwesomeVersion
from typing import Union

from homeassistant.helpers import discovery
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.utility_meter import DOMAIN as UTILITY_DOMAIN
from homeassistant.components.utility_meter import (
    DEFAULT_OFFSET,
)
from homeassistant.components.utility_meter.const import (
    CONF_METER_NET_CONSUMPTION,
    DATA_UTILITY,
    DATA_TARIFF_SENSORS,
    CONF_METER_TYPE,
    CONF_SOURCE_SENSOR,
    CONF_TARIFFS
)
from homeassistant.components.utility_meter.sensor import UtilityMeterSensor
from homeassistant.const import __short_version__

from custom_components.powercalc.const import (
    CONF_CREATE_UTILITY_METERS,
    CONF_UTILITY_METER_TYPES,
)
from custom_components.powercalc.sensors.energy import VirtualEnergySensor
from custom_components.powercalc.sensors.group import GroupedEnergySensor
from homeassistant.helpers.typing import HomeAssistantType

_LOGGER = logging.getLogger(__name__)


def create_utility_meters(
    hass: HomeAssistantType,
    energy_sensor: Union[VirtualEnergySensor, GroupedEnergySensor],
    sensor_config: dict,
) -> list[UtilityMeterSensor]:
    """Create the utility meters"""
    utility_meters = []

    if not sensor_config.get(CONF_CREATE_UTILITY_METERS):
        return []

    meter_types = sensor_config.get(CONF_UTILITY_METER_TYPES)
    for meter_type in meter_types:
        name = f"{energy_sensor.name} {meter_type}"
        entity_id = f"{energy_sensor.entity_id}_{meter_type}"
        _LOGGER.debug("Creating utility_meter sensor: %s", name)

        # Below is for BC purposes. Can be removed somewhere in the future
        if AwesomeVersion(__short_version__) < "2021.10":
            utility_meter = VirtualUtilityMeterSensor(
                energy_sensor.entity_id, name, meter_type, entity_id
            )
        else:
            if not DATA_UTILITY in hass.data:
                hass.data[DATA_UTILITY] = {}
            hass.data[DATA_UTILITY][entity_id] = {
                CONF_SOURCE_SENSOR: energy_sensor.entity_id,
                CONF_METER_TYPE: meter_type,
                CONF_TARIFFS: [],
                CONF_METER_NET_CONSUMPTION: False
            }

            utility_meter = UtilityMeterSensor(
                parent_meter=entity_id,
                source_entity=energy_sensor.entity_id,
                name=name,
                meter_type=meter_type,
                meter_offset=DEFAULT_OFFSET,
                net_consumption=False
            )

            hass.data[DATA_UTILITY][entity_id][DATA_TARIFF_SENSORS] = [
                utility_meter
            ]
        utility_meters.append(utility_meter)

    return utility_meters


class VirtualUtilityMeterSensor(UtilityMeterSensor):
    """Utility meter resets on each cycle (daily, hourly etc)"""

    def __init__(self, source_entity, name, meter_type, entity_id):
        super().__init__(source_entity, name, meter_type, DEFAULT_OFFSET, False)
        self.entity_id = entity_id