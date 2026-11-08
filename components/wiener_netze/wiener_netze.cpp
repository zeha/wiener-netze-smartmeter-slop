#include "wiener_netze.h"

#include <cinttypes>
#include <cstdio>

#include "esphome/core/hal.h"
#include "esphome/core/log.h"

namespace esphome {
namespace wiener_netze {

static const char *const TAG = "wiener_netze";

// A pause this long inside a frame means the frame was cut off; start over.
static const uint32_t INTER_BYTE_TIMEOUT_MS = 200;

static uint32_t read_be(const uint8_t *data, size_t offset, size_t length) {
  uint32_t result = 0;
  for (size_t i = offset; i < offset + length; i++)
    result = (result << 8) | data[i];
  return result;
}

// CRC-16/X-25 (HDLC FCS): reflected poly 0x1021, init 0xFFFF, final XOR 0xFFFF.
static uint16_t crc16_x25(const uint8_t *data, size_t length) {
  uint16_t crc = 0xFFFF;
  for (size_t i = 0; i < length; i++) {
    crc ^= data[i];
    for (int bit = 0; bit < 8; bit++)
      crc = (crc & 1) ? (crc >> 1) ^ 0x8408 : crc >> 1;
  }
  return crc ^ 0xFFFF;
}

void WienerNetze::set_security_key(std::initializer_list<uint8_t> key) {
  size_t i = 0;
  for (uint8_t b : key) {
    if (i < this->key_.size())
      this->key_[i++] = b;
  }
}

void WienerNetze::setup() {
  mbedtls_aes_init(&this->aes_);
  mbedtls_aes_setkey_enc(&this->aes_, this->key_.data(), 128);
  this->start_time_ = millis();
}

void WienerNetze::dump_config() {
  ESP_LOGCONFIG(TAG,
                "Wiener Netze smart meter (IR push telegrams):\n"
                "  Frame length: %u bytes\n"
                "  Read timeout: %" PRIu32 " ms",
                (unsigned) FRAME_LENGTH, this->read_timeout_);
  this->check_uart_settings(9600, 1, uart::UART_CONFIG_PARITY_NONE, 8);
}

void WienerNetze::loop() {
  const uint32_t now = millis();
  if (this->receiving_ && now - this->last_byte_time_ > INTER_BYTE_TIMEOUT_MS) {
    ESP_LOGW(TAG, "Incomplete frame (%u of %u bytes), discarding", (unsigned) this->pos_, (unsigned) FRAME_LENGTH);
    this->receiving_ = false;
  }

  uint8_t byte;
  while (this->available() > 0 && this->read_byte(&byte)) {
    this->last_byte_time_ = now;
    if (!this->receiving_) {
      // Every frame starts with 7E A0
      if (this->previous_byte_ == 0x7E && byte == 0xA0) {
        this->frame_[0] = 0x7E;
        this->frame_[1] = 0xA0;
        this->pos_ = 2;
        this->receiving_ = true;
      }
    } else {
      this->frame_[this->pos_++] = byte;
      if (this->pos_ == FRAME_LENGTH) {
        this->receiving_ = false;
        this->handle_frame_();
      }
    }
    this->previous_byte_ = byte;
  }

  if (!this->timeout_warned_ && this->telegram_count_ == 0 && now - this->start_time_ > this->read_timeout_) {
    ESP_LOGW(TAG, "No valid telegram within %" PRIu32 " ms; check IR head alignment, wiring and security key",
             this->read_timeout_);
    this->timeout_warned_ = true;
  }
}

bool WienerNetze::check_crc_() const {
  // FCS covers everything between the opening flag and the FCS itself
  const uint16_t crc = crc16_x25(this->frame_.data() + 1, FRAME_LENGTH - 4);
  const uint16_t expected = (this->frame_[FRAME_LENGTH - 2] << 8) | this->frame_[FRAME_LENGTH - 3];
  if (crc != expected) {
    ESP_LOGW(TAG, "CRC check failed (got %04X, expected %04X)", crc, expected);
    return false;
  }
  return true;
}

void WienerNetze::handle_frame_() {
  if (!this->check_crc_())
    return;

  // AES-128-GCM payload decrypted as CTR: IV = system title (8) + frame counter (4) + counter 2
  uint8_t iv[16] = {0};
  memcpy(iv, this->frame_.data() + HEADER_LENGTH, 8);
  memcpy(iv + 8, this->frame_.data() + HEADER_LENGTH + 10, 4);
  iv[15] = 0x02;

  uint8_t plain[PAYLOAD_LENGTH];
  size_t nc_off = 0;
  uint8_t stream_block[16] = {0};
  if (mbedtls_aes_crypt_ctr(&this->aes_, PAYLOAD_LENGTH, &nc_off, iv, stream_block,
                            this->frame_.data() + HEADER_LENGTH + 14, plain) != 0) {
    ESP_LOGW(TAG, "Decryption failed");
    return;
  }

  const uint32_t year = read_be(plain, PAYLOAD_LENGTH - 52, 2);
  const uint32_t month = plain[PAYLOAD_LENGTH - 50];
  const uint32_t day = plain[PAYLOAD_LENGTH - 49];
  const uint32_t hour = plain[PAYLOAD_LENGTH - 47];
  const uint32_t minute = plain[PAYLOAD_LENGTH - 46];
  const uint32_t second = plain[PAYLOAD_LENGTH - 45];
  // A wrong key decrypts to garbage that still passes the CRC; reject implausible dates
  if (year < 2000 || year > 2099 || month < 1 || month > 12 || day < 1 || day > 31 || hour > 23 || minute > 59 ||
      second > 59) {
    ESP_LOGW(TAG, "Decrypted telegram has no valid timestamp; is the security key correct?");
    return;
  }

  uint32_t values[VALUE_COUNT];
  for (size_t i = 0; i < VALUE_COUNT; i++)
    values[i] = read_be(plain, PAYLOAD_LENGTH - 39 + 5 * i, 4);

  this->telegram_count_++;
  char timestamp[20];
  snprintf(timestamp, sizeof(timestamp), "%04" PRIu32 "-%02" PRIu32 "-%02" PRIu32 " %02" PRIu32 ":%02" PRIu32
           ":%02" PRIu32, year, month, day, hour, minute, second);
  ESP_LOGD(TAG, "Telegram %s: +A=%" PRIu32 " Wh -A=%" PRIu32 " Wh +P=%" PRIu32 " W -P=%" PRIu32 " W", timestamp,
           values[0], values[1], values[4], values[5]);

  for (size_t i = 0; i < VALUE_COUNT; i++) {
    if (this->value_sensors_[i] == nullptr)
      continue;
    // energy registers are Wh / varh, published as kWh / kvarh
    this->value_sensors_[i]->publish_state(i < 4 ? values[i] / 1000.0f : (float) values[i]);
  }
  if (this->timestamp_sensor_ != nullptr)
    this->timestamp_sensor_->publish_state(timestamp);
  if (this->telegram_count_sensor_ != nullptr)
    this->telegram_count_sensor_->publish_state(this->telegram_count_);
  for (auto *trigger : this->triggers_)
    trigger->trigger();
}

}  // namespace wiener_netze
}  // namespace esphome
