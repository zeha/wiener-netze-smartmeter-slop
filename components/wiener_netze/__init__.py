import esphome.codegen as cg
from esphome import automation
from esphome.components import uart
import esphome.config_validation as cv
from esphome.const import CONF_ID, CONF_TRIGGER_ID

CODEOWNERS = []
DEPENDENCIES = ["uart"]
MULTI_CONF = True

CONF_WIENER_NETZE_ID = "wiener_netze_id"
CONF_SECURITY_KEY = "security_key"
CONF_READ_TIMEOUT = "read_timeout"
CONF_ON_TELEGRAM = "on_telegram"

wiener_netze_ns = cg.esphome_ns.namespace("wiener_netze")
WienerNetze = wiener_netze_ns.class_("WienerNetze", cg.Component, uart.UARTDevice)
TelegramTrigger = automation.Trigger.template()


def validate_security_key(value):
    value = cv.string_strict(value).strip()
    if len(value) != 32:
        raise cv.Invalid(
            f"security_key must be exactly 32 hex characters (got {len(value)})"
        )
    try:
        bytes.fromhex(value)
    except ValueError as err:
        raise cv.Invalid("security_key must contain only hex characters") from err
    return value.lower()


# cv.sensitive masks the key in dumps; it only exists in newer ESPHome releases
_sensitive = getattr(cv, "sensitive", lambda inner: inner)


CONFIG_SCHEMA = (
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(WienerNetze),
            cv.Required(CONF_SECURITY_KEY): _sensitive(validate_security_key),
            cv.Optional(
                CONF_READ_TIMEOUT, default="10s"
            ): cv.positive_time_period_milliseconds,
            cv.Optional(CONF_ON_TELEGRAM): automation.validate_automation(
                {cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(TelegramTrigger)}
            ),
        }
    )
    .extend(cv.COMPONENT_SCHEMA)
    .extend(uart.UART_DEVICE_SCHEMA)
)

FINAL_VALIDATE_SCHEMA = uart.final_validate_device_schema(
    "wiener_netze",
    baud_rate=9600,
    require_rx=True,
    data_bits=8,
    parity="NONE",
    stop_bits=1,
)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await uart.register_uart_device(var, config)
    key = bytes.fromhex(config[CONF_SECURITY_KEY])
    cg.add(var.set_security_key(list(key)))
    cg.add(var.set_read_timeout(config[CONF_READ_TIMEOUT]))
    for conf in config.get(CONF_ON_TELEGRAM, []):
        trigger = cg.new_Pvariable(conf[CONF_TRIGGER_ID])
        cg.add(var.add_on_telegram_trigger(trigger))
        await automation.build_automation(trigger, [], conf)
