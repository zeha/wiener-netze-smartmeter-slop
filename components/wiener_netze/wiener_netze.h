#pragma once

#include <array>
#include <cstdint>
#include <initializer_list>
#include <vector>

#include "esphome/core/automation.h"
#include "esphome/core/component.h"
#include "esphome/core/defines.h"
#include "esphome/components/uart/uart.h"
// ESPHome only copies a component's sources into the build when the YAML loads
// it, so sensor/text_sensor are optional: a config without a `sensor:` or
// `text_sensor:` block must still compile.
#ifdef USE_SENSOR
#include "esphome/components/sensor/sensor.h"
#endif
#ifdef USE_TEXT_SENSOR
#include "esphome/components/text_sensor/text_sensor.h"
#endif

#include "mbedtls/aes.h"

namespace esphome {
namespace wiener_netze {

// Iskraemeko / Landis+Gyr push telegram layout (Wiener Netze M1), ported from
// aldadic/esp-smartmeter-reader (Landis+Gyr and Iskraemeco settings).
static const size_t FRAME_LENGTH = 105;
static const size_t HEADER_LENGTH = 14;  // offset of the system title
static const size_t PAYLOAD_LENGTH = FRAME_LENGTH - HEADER_LENGTH - 17;  // 74 bytes
static const size_t VALUE_COUNT = 8;  // +A, -A, +R, -R, +P, -P, +Q, -Q

class WienerNetze : public Component, public uart::UARTDevice {
 public:
  void setup() override;
  void loop() override;
  void dump_config() override;
  float get_setup_priority() const override { return setup_priority::DATA; }

  void set_security_key(std::initializer_list<uint8_t> key);
  void set_read_timeout(uint32_t read_timeout) { this->read_timeout_ = read_timeout; }
#ifdef USE_SENSOR
  void set_value_sensor(size_t index, sensor::Sensor *sens) { this->value_sensors_[index] = sens; }
  void set_telegram_count_sensor(sensor::Sensor *sens) { this->telegram_count_sensor_ = sens; }
#endif
#ifdef USE_TEXT_SENSOR
  void set_timestamp_sensor(text_sensor::TextSensor *sens) { this->timestamp_sensor_ = sens; }
#endif
  void add_on_telegram_trigger(Trigger<> *trigger) { this->triggers_.push_back(trigger); }

 protected:
  bool check_crc_() const;
  void handle_frame_();

  std::array<uint8_t, 16> key_{};
  mbedtls_aes_context aes_;
  uint32_t read_timeout_{10000};
  uint32_t start_time_{0};
  bool timeout_warned_{false};

  std::array<uint8_t, FRAME_LENGTH> frame_{};
  size_t pos_{0};
  bool receiving_{false};
  uint8_t previous_byte_{0};
  uint32_t last_byte_time_{0};
  uint32_t telegram_count_{0};

#ifdef USE_SENSOR
  std::array<sensor::Sensor *, VALUE_COUNT> value_sensors_{};
  sensor::Sensor *telegram_count_sensor_{nullptr};
#endif
#ifdef USE_TEXT_SENSOR
  text_sensor::TextSensor *timestamp_sensor_{nullptr};
#endif
  std::vector<Trigger<> *> triggers_;
};

}  // namespace wiener_netze
}  // namespace esphome
