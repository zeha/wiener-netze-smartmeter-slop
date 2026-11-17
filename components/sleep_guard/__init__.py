import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import esp32
from esphome.const import CONF_ID, CONF_RUN_DURATION, CONF_SLEEP_DURATION

CODEOWNERS = ["@zeha"]
DEPENDENCIES = ["esp32"]

sleep_guard_ns = cg.esphome_ns.namespace("sleep_guard")
DeepSleepComponent = cg.esphome_ns.namespace("deep_sleep").class_("DeepSleepComponent")
SleepGuard = sleep_guard_ns.class_("SleepGuard", cg.Component)

CONF_DEEP_SLEEP_ID = "deep_sleep_id"
CONF_AWAKE_MARGIN = "awake_margin"
CONF_STALL_TIMEOUT = "stall_timeout"

CONFIG_SCHEMA = cv.All(
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(SleepGuard),
            cv.Optional(CONF_DEEP_SLEEP_ID): cv.use_id(DeepSleepComponent),
            # Must mirror the linked deep_sleep component's run_duration /
            # sleep_duration: together with awake_margin they define how long
            # the device may stay awake after boot before sleep_guard forces
            # a sleep entry.
            cv.Optional(CONF_RUN_DURATION, default="40s"): cv.positive_time_period_milliseconds,
            cv.Optional(CONF_SLEEP_DURATION, default="5min"): cv.positive_time_period_milliseconds,
            cv.Optional(CONF_AWAKE_MARGIN, default="10min"): cv.positive_time_period_milliseconds,
            # Restart the device if the main loop stops running for this long
            # (main task stuck in the deep-sleep teardown).
            cv.Optional(CONF_STALL_TIMEOUT, default="2min"): cv.positive_time_period_milliseconds,
        }
    ),
    cv.only_on(["esp32"]),
)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    if deep_sleep_id := config.get(CONF_DEEP_SLEEP_ID):
        dep = await cg.get_variable(deep_sleep_id)
        cg.add(var.set_deep_sleep_component(dep))
    cg.add(var.set_run_duration(config[CONF_RUN_DURATION].total_milliseconds))
    cg.add(var.set_sleep_duration(config[CONF_SLEEP_DURATION].total_milliseconds))
    cg.add(var.set_awake_margin(config[CONF_AWAKE_MARGIN].total_milliseconds))
    cg.add(var.set_stall_timeout(config[CONF_STALL_TIMEOUT].total_milliseconds))
