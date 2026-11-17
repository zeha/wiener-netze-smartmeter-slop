#include "sleep_guard.h"

#include <cinttypes>

#include "esphome/components/deep_sleep/deep_sleep_component.h"
#include "esphome/core/hal.h"
#include "esphome/core/log.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

namespace esphome::sleep_guard {
static const char *const TAG = "sleep_guard";

// Grace after boot before stall checking starts: the WiFi connect, the
// component setup, and the on_telegram automation (wait_until up to 20s plus
// 1s) can all legitimately hold the main loop.
static const uint32_t STALL_GRACE_MS = 120000;
static const uint32_t WATCHDOG_CHECK_PERIOD_MS = 5000;

// Own FreeRTOS task: keeps running while the main loop task is blocked,
// which is exactly when it is needed. Static member so it can call the
// protected check_stall_().
void SleepGuard::watchdog_task_(void *arg) {
  auto *self = static_cast<SleepGuard *>(arg);
  for (;;) {
    vTaskDelay(pdMS_TO_TICKS(WATCHDOG_CHECK_PERIOD_MS));
    self->check_stall_();
  }
}

void SleepGuard::setup() {
  this->last_loop_ms_ = millis();
  if (this->deep_sleep_component_ != nullptr) {
    const uint32_t awake_check_ms =
        this->run_duration_ms_ + this->sleep_duration_ms_ + this->awake_margin_ms_;
    ESP_LOGI(TAG,
             "Forces a sleep entry if still awake %" PRIu32 " ms after boot (run %" PRIu32
             " ms + sleep %" PRIu32 " ms + margin %" PRIu32 " ms)",
             awake_check_ms, this->run_duration_ms_, this->sleep_duration_ms_,
             this->awake_margin_ms_);
    this->set_timeout("sleep-guard-forced-sleep", awake_check_ms, [this]() {
      ESP_LOGW(TAG,
               "Still awake %" PRIu32 " ms after boot - the sleep entry never completed; "
               "forcing it",
               millis());
      this->deep_sleep_component_->begin_sleep(/*manual=*/true);
    });
  } else {
    ESP_LOGW(TAG, "No deep_sleep_id set - only the main-loop stall guard is active");
  }
  if (xTaskCreate(&SleepGuard::watchdog_task_, "sleep_guard", 8192, this, 1, nullptr) != pdPASS) {
    ESP_LOGE(TAG, "Could not create the watchdog task - the stall guard is disabled");
  }
}

void SleepGuard::loop() { this->last_loop_ms_ = millis(); }

void SleepGuard::check_stall_() {
  const uint32_t now = millis();
  if (now < STALL_GRACE_MS)
    return;
  const uint32_t idle = now - this->last_loop_ms_;
  if (idle > this->stall_timeout_ms_) {
    ESP_LOGE(TAG,
             "Main loop has not run for %" PRIu32 " ms (limit %" PRIu32
             " ms). Restarting: the deep-sleep entry did not complete and consumed the "
             "one-shot wake timer - without a restart the device would stay awake forever.",
             idle, this->stall_timeout_ms_);
    arch_restart();
  }
}

void SleepGuard::dump_config() {
  ESP_LOGCONFIG(TAG, "Sleep Guard");
  ESP_LOGCONFIG(TAG, "  deep_sleep component: %s",
                this->deep_sleep_component_ != nullptr ? "linked" : "none (stall guard only)");
  ESP_LOGCONFIG(TAG, "  run duration: %" PRIu32 " ms", this->run_duration_ms_);
  ESP_LOGCONFIG(TAG, "  sleep duration: %" PRIu32 " ms", this->sleep_duration_ms_);
  ESP_LOGCONFIG(TAG, "  awake margin: %" PRIu32 " ms", this->awake_margin_ms_);
  ESP_LOGCONFIG(TAG, "  stall timeout: %" PRIu32 " ms", this->stall_timeout_ms_);
}

}  // namespace esphome::sleep_guard
