import esphome.codegen as cg
from esphome.components import text_sensor
import esphome.config_validation as cv
from esphome.const import CONF_TYPE

from . import CONF_WIENER_NETZE_ID, WienerNetze

DEPENDENCIES = ["wiener_netze"]

CONFIG_SCHEMA = text_sensor.text_sensor_schema(icon="mdi:clock-outline").extend(
    {
        cv.GenerateID(CONF_WIENER_NETZE_ID): cv.use_id(WienerNetze),
        cv.Optional(CONF_TYPE, default="timestamp"): cv.one_of("timestamp", lower=True),
    }
)


async def to_code(config):
    parent = await cg.get_variable(config[CONF_WIENER_NETZE_ID])
    sens = await text_sensor.new_text_sensor(config)
    cg.add(parent.set_timestamp_sensor(sens))
