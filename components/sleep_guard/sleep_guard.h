#pragma once

#include <cstdint>

#include "esphome/core/component.h"

namespace esphome::deep_sleep {
class DeepSleepComponent;
}

namespace esphome::sleep_guard {

/// Safety net for deep-sleep entry failure.
///
/// deep_sleep arms a one-shot RTC wake timer at boot and begin_sleep()
/// consumes it. If sleep entry never completes - the main task blocks in
/// teardown, or the attempt is skipped - the timer is not re-armed and the
/// device stays awake forever with the pipeline dead: the 2026-11-16
/// 10:44-13:41 outage (see projects/wiener-netze-smartmeter/decisions/
/// deep-sleep-hang-root-cause-wake-timer-consumed.md in the vault).
///
/// Two independent guards:
///
/// 1. A separate FreeRTOS watchdog task: restarts the device if the main
///    loop has not run for stall_timeout. Needed because the loop task is
///    not registered with the task WDT and on the ESP32-S2 the idle task on
///    the other core keeps the TWDT fed - a blocked main task never trips
///    a hardware reset (the device stayed powered for three hours on
///    2026-11-16).
/// 2. If the device is still awake after run_duration + sleep_duration +
///    awake_margin since boot, force a sleep entry via
///    begin_sleep(manual=true). If that wedges, guard 1 restarts.
class SleepGuard : public Component {
 public:
  void set_deep_sleep_component(deep_sleep::DeepSleepComponent *component) {
    this->deep_sleep_component_ = component;
  }
  void set_run_duration(uint32_t ms) { this->run_duration_ms_ = ms; }
  void set_sleep_duration(uint32_t ms) { this->sleep_duration_ms_ = ms; }
  void set_awake_margin(uint32_t ms) { this->awake_margin_ms_ = ms; }
  void set_stall_timeout(uint32_t ms) { this->stall_timeout_ms_ = ms; }

  float get_setup_priority() const override { return setup_priority::DATA; }
  void setup() override;
  void loop() override;
  void dump_config() override;

 protected:
  static void watchdog_task_(void *arg);
  void check_stall_();

  deep_sleep::DeepSleepComponent *deep_sleep_component_{nullptr};
  uint32_t run_duration_ms_{40000};
  uint32_t sleep_duration_ms_{300000};
  uint32_t awake_margin_ms_{600000};
  uint32_t stall_timeout_ms_{120000};
  volatile uint32_t last_loop_ms_{0};
};

}  // namespace esphome::sleep_guard
