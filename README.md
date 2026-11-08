# Wiener Netze smart meter for ESPHome

An [ESPHome](https://esphome.io) external component, `wiener_netze`, that reads the
customer interface (Kundenschnittstelle) of the Wiener Netze M1 smart meter
(Iskraemeko, also Landis+Gyr E450 with the same frame layout) through its IR
window, decrypts the push telegrams and exposes the values to Home Assistant.

The meter pushes an encrypted DLMS/COSEM telegram in an HDLC frame (105 bytes)
about once per second, receive only, 9600 baud 8N1. The component:

- waits for the `7E A0` frame start and collects 105 bytes,
- checks the CRC-16/X-25 frame checksum,
- decrypts the payload with AES-128 (CTR, which is GCM without the tag check)
  using your security key; the IV is the system title (frame bytes 14..21) plus
  the frame counter (bytes 24..27) plus `00 00 00 02`,
- reads the meter time and eight registers at fixed offsets and publishes them,
- drops frames whose decrypted timestamp is not plausible (typically a wrong key),
- logs one warning if no valid telegram arrived within `read_timeout` after boot.

The logic is a port of [aldadic/esp-smartmeter-reader](https://github.com/aldadic/esp-smartmeter-reader)
(GPL-3.0); see [LICENSE](LICENSE).

## Hardware

- Wemos (LOLIN) S2 Mini: ESP32-S2, 4 MB flash, 2 MB PSRAM. ESPHome board id `lolin_s2_mini`.
- A passive IR read head (phototransistor, 3.3 V logic), e.g. the common "IR Lesekopf TTL" types.

| IR head | S2 Mini |
|---------|---------|
| VCC     | 3V3     |
| GND     | GND     |
| Data (TX of the head) | GPIO21 |

No TX line is needed: the meter only sends. If nothing arrives at all, the head
may output an inverted signal; set `inverted: true` on the `rx_pin` (see the
example config). The S2 Mini logs over its native USB port, so the hardware UART
is free for the meter.

### Battery voltage divider

The example config measures the battery of the 7000 mAh LiPo:

| Part | Connection |
|------|------------|
| R1 = 1 MOhm | battery + terminal -> GPIO3 |
| R2 = 1 MOhm | GPIO3 -> GND |
| C = 100 nF (optional) | GPIO3 -> GND, against noise |

GPIO3 is on ADC1, which keeps working while WiFi is on (ADC2 does not). The
divider halves the cell voltage (4.2 V full -> 2.1 V at the pin), inside the
range of the 12 dB attenuation. Tap the battery's own + terminal, before any
regulator. Do not measure the board's 3V3 pin or rail: it is regulated, so it
reads about 3.3 V until the battery is almost empty and says nothing about the
charge. Also, never connect a LiPo (up to 4.2 V) straight to the 3V3 pin. Feed
it through a regulator to 3V3, or into the 5V/VBUS pin and the on-board LDO.

The divider draws about 2 uA continuously (4.2 V / 2 MOhm), negligible against
7000 mAh. With 1 MOhm resistors the source is high-impedance; the 100 nF
capacitor gives the ADC a stable charge to sample and makes readings noticeably
steadier.

## Configuration

See [config/example_smartmeter.yaml](config/example_smartmeter.yaml) for a complete device.

```yaml
external_components:
  - source: github://zeha/wiener-netze-smartmeter@main
    components: [wiener_netze]

uart:
  id: meter_uart
  rx_pin: GPIO21
  baud_rate: 9600

wiener_netze:
  uart_id: meter_uart
  security_key: "0123456789abcdef0123456789abcdef"  # placeholder: your key from the portal
  read_timeout: 10s        # optional, default 10s
  on_telegram:             # optional, runs after every decoded telegram
    - logger.log: "telegram"

sensor:
  - platform: wiener_netze
    type: energy_active_plus
    name: "Energy import"

text_sensor:
  - platform: wiener_netze
    type: timestamp
    name: "Meter time"
```

The security key (32 hex characters, "Schlüssel" for the customer interface) is
shown in the Wiener Netze Smart Meter portal after the interface has been
activated. Keep it in `secrets.yaml` (`security_key: !secret meter_key`).

### Sensor types

| `type` | Unit | Device class | State class |
|--------|------|--------------|-------------|
| `energy_active_plus` (+A, import) | kWh | energy | total_increasing |
| `energy_active_minus` (-A, export) | kWh | energy | total_increasing |
| `energy_reactive_plus` (+R) | kvarh | reactive_energy | total_increasing |
| `energy_reactive_minus` (-R) | kvarh | reactive_energy | total_increasing |
| `power_active_plus` (+P) | W | power | measurement |
| `power_active_minus` (-P) | W | power | measurement |
| `power_reactive_plus` (+Q) | var | reactive_power | measurement |
| `power_reactive_minus` (-Q) | var | reactive_power | measurement |
| `telegram_count` | | | total_increasing (diagnostic; resets on every boot/wake) |

Text sensor `type: timestamp` (default): meter time as `YYYY-MM-DD HH:MM:SS`
(local meter time, no time zone).

The meter sends energy in Wh/varh; the component divides by 1000, as the
reference sketch does. All of these are standard ESPHome sensors, so filters,
names and ids work as usual. ESPHome sensor values are 32-bit floats: above
about 16 777 kWh the import counter loses its last Wh digit.

## Battery operation

The example sleeps with `deep_sleep` and wakes every 5 minutes (`sleep_duration`;
1 to 10 minutes are sensible). One telegram per wake-up is enough since the
meter pushes about every second. The `on_telegram` automation waits until Home
Assistant is connected, then puts the board back to sleep; `run_duration: 40s`
is the fallback when no telegram or no WiFi comes. To keep the wake time short:

- use a static IP (`manual_ip`) and `fast_connect: true`,
- keep the logger at `INFO` or lower once it works,
- the S2 Mini has a power LED and a USB regulator with quiescent current; for
  long battery life power it from a LiPo through an efficient 3.3 V regulator to
  the 3V3 pin, and consider removing the power LED (see the voltage divider
  above for measuring the battery).

Battery sensors: `Smartmeter battery voltage` (V) is sampled once per wake-up,
right after boot (`esphome.on_boot` at priority 500, before WiFi starts), as
the average of 64 ADC readings multiplied by 2 for the divider.
`Smartmeter battery level` (%) maps that voltage with a rough LiPo curve:
>= 4.15 V 100 %, 4.05 V 85 %, 3.95 V 70 %, 3.85 V 55 %, 3.75 V 40 %,
3.65 V 25 %, 3.55 V 12 %, 3.45 V 5 %, below 0 %. Under WiFi transmit load the
cell sags a little, and the ESP32 ADC is accurate to only a few percent, so
treat both values as estimates, good enough as a reminder to recharge.

The energy sensors are `total_increasing`, so gaps while the board sleeps do not
disturb Home Assistant's energy dashboard. To flash a sleeping board over the
air, turn on OTA mode by preventing sleep (e.g. a `deep_sleep.prevent` from a
Home Assistant helper), or flash it over USB.

## Development

See [AGENTS.md](AGENTS.md). The test in [test/](test/) checks the frame logic
against a synthetic telegram; [test/README.md](test/README.md) explains how to
capture a real one.
