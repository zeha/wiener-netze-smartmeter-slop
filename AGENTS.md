# wiener-netze-smartmeter — agent instructions

## Purpose

ESPHome external component `wiener_netze` that decrypts the Wiener Netze M1 smart
meter's IR push telegrams (105-byte HDLC frames, AES-128) and publishes them as
Home Assistant sensors, plus an example config for a battery-powered Wemos S2 Mini.

## Build, test, run

```sh
python3 -m venv .venv
.venv/bin/pip install esphome pycryptodome
.venv/bin/esphome config config/example_smartmeter.yaml    # schema check
.venv/bin/esphome compile config/example_smartmeter.yaml   # full firmware build
.venv/bin/python test/decrypt_test.py                      # Python mirror of the frame logic
```

The first compile downloads ESP-IDF and the toolchain (several GB, many minutes);
later builds are incremental. Verified with ESPHome 2026.10.2, ESP-IDF 5.5.6.
Flashing: `.venv/bin/esphome run config/example_smartmeter.yaml` with the board on USB.

## Conventions

- Component code lives in `components/wiener_netze/`: ESPHome's `github://`
  external_components source looks for `components/` (or `esphome/components/`)
  at the repo root. The example config uses a `type: local` source `../components`.
- ESPHome has no `manifest.yaml`; dependencies are `DEPENDENCIES = ["uart"]` in `__init__.py`.
- Frame constants and offsets (length 105, header 14, payload 74, IV, CRC byte
  order, value offsets) are ported 1:1 from aldadic/esp-smartmeter-reader.
  Change them only together with `test/decrypt_test.py`, which mirrors them.
- ESP32 board id for the Wemos S2 Mini is `lolin_s2_mini` (`wemos_s2_mini` does not exist).
- `api.encryption.key` must not be all zeros (ESPHome rejects it); the example
  uses a visible non-zero placeholder.
- C++ follows ESPHome style: `this->`, trailing `_` for protected members, `ESP_LOG*` with `TAG`.

## Do not

- Commit a real security key, WiFi credentials or a captured frame together
  with its key. `secrets.yaml` and `test/vectors.json` are gitignored.
- Use `.ref/` for anything but reading: it holds gitignored upstream reference checkouts.

## Where decisions live

README.md (behaviour, wiring, battery notes) and this file; the Owncore vault
project note, if one exists, for status.
