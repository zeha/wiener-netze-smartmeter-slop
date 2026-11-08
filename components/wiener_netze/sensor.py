import esphome.codegen as cg
from esphome.components import sensor
import esphome.config_validation as cv
from esphome.const import (
    CONF_TYPE,
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_REACTIVE_ENERGY,
    DEVICE_CLASS_REACTIVE_POWER,
    ENTITY_CATEGORY_DIAGNOSTIC,
    STATE_CLASS_MEASUREMENT,
    STATE_CLASS_TOTAL_INCREASING,
    UNIT_KILOVOLT_AMPS_REACTIVE_HOURS,
    UNIT_KILOWATT_HOURS,
    UNIT_VOLT_AMPS_REACTIVE,
    UNIT_WATT,
)

from . import CONF_WIENER_NETZE_ID, WienerNetze

DEPENDENCIES = ["wiener_netze"]

# type -> index into WienerNetze's value slots (order of the meter's push telegram)
TYPES = {
    "energy_active_plus": 0,
    "energy_active_minus": 1,
    "energy_reactive_plus": 2,
    "energy_reactive_minus": 3,
    "power_active_plus": 4,
    "power_active_minus": 5,
    "power_reactive_plus": 6,
    "power_reactive_minus": 7,
}
TELEGRAM_COUNT = "telegram_count"

_ENERGY = sensor.sensor_schema(
    unit_of_measurement=UNIT_KILOWATT_HOURS,
    accuracy_decimals=3,
    device_class=DEVICE_CLASS_ENERGY,
    state_class=STATE_CLASS_TOTAL_INCREASING,
)
_REACTIVE_ENERGY = sensor.sensor_schema(
    unit_of_measurement=UNIT_KILOVOLT_AMPS_REACTIVE_HOURS,
    accuracy_decimals=3,
    device_class=DEVICE_CLASS_REACTIVE_ENERGY,
    state_class=STATE_CLASS_TOTAL_INCREASING,
)
_POWER = sensor.sensor_schema(
    unit_of_measurement=UNIT_WATT,
    accuracy_decimals=0,
    device_class=DEVICE_CLASS_POWER,
    state_class=STATE_CLASS_MEASUREMENT,
)
_REACTIVE_POWER = sensor.sensor_schema(
    unit_of_measurement=UNIT_VOLT_AMPS_REACTIVE,
    accuracy_decimals=0,
    device_class=DEVICE_CLASS_REACTIVE_POWER,
    state_class=STATE_CLASS_MEASUREMENT,
)
_COUNT = sensor.sensor_schema(
    icon="mdi:counter",
    accuracy_decimals=0,
    state_class=STATE_CLASS_TOTAL_INCREASING,
    entity_category=ENTITY_CATEGORY_DIAGNOSTIC,
)

_PARENT = cv.Schema({cv.GenerateID(CONF_WIENER_NETZE_ID): cv.use_id(WienerNetze)})

CONFIG_SCHEMA = cv.typed_schema(
    {
        "energy_active_plus": _ENERGY.extend(_PARENT),
        "energy_active_minus": _ENERGY.extend(_PARENT),
        "energy_reactive_plus": _REACTIVE_ENERGY.extend(_PARENT),
        "energy_reactive_minus": _REACTIVE_ENERGY.extend(_PARENT),
        "power_active_plus": _POWER.extend(_PARENT),
        "power_active_minus": _POWER.extend(_PARENT),
        "power_reactive_plus": _REACTIVE_POWER.extend(_PARENT),
        "power_reactive_minus": _REACTIVE_POWER.extend(_PARENT),
        TELEGRAM_COUNT: _COUNT.extend(_PARENT),
    },
    key=CONF_TYPE,
)


async def to_code(config):
    parent = await cg.get_variable(config[CONF_WIENER_NETZE_ID])
    sens = await sensor.new_sensor(config)
    if config[CONF_TYPE] == TELEGRAM_COUNT:
        cg.add(parent.set_telegram_count_sensor(sens))
    else:
        cg.add(parent.set_value_sensor(TYPES[config[CONF_TYPE]], sens))
