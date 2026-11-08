# Test vectors

`decrypt_test.py` mirrors the component's frame logic in Python (CRC-16/X-25,
AES-128-CTR, fixed offsets) and checks it against a **synthetic** frame: a known
plaintext encrypted with AES-128-GCM, the meter's cipher. Neither reference
repository (aldadic/esp-smartmeter-reader, tofuSCHNITZEL/wiener_netze_smartmeter)
publishes a captured telegram from a real meter, in code, tests or issues.

```sh
.venv/bin/pip install pycryptodome   # once
.venv/bin/python test/decrypt_test.py
```

## Capturing a real telegram on the bench

1. Connect the IR read head to a USB serial adapter (or to the ESP and log raw
   UART bytes with ESPHome's `uart: debug:` option) and place it on the meter's
   IR window.
2. Open a serial monitor at **9600 baud, 8N1** in hex mode, e.g.
   `python -m serial.tools.miniterm --raw /dev/ttyUSB0 9600` piped through
   `xxd`, or `picocom -b 9600 --imap spchex /dev/ttyUSB0`.
3. Telegrams arrive about once per second. Copy one complete frame: **105
   bytes**, starting with `7E A0` and ending with `7E`.
4. Note the values on the meter display at that moment (+A in kWh, +P in W) and
   get the 32-hex-character security key from the Wiener Netze Smart Meter portal.
5. Create `test/vectors.json` (it is gitignored, because it holds your key):

   ```json
   [
     {
       "name": "my meter, 2026-11-08",
       "key": "<32 hex chars from the portal>",
       "frame": "7ea0...7e",
       "expected": {"timestamp": "2026-11-08 14:30:45", "energy_active_plus": 1234.567}
     }
   ]
   ```

6. Run the test again; it checks every entry in `vectors.json`.

Do not commit a frame together with its real key. To share a fixture publicly,
use a meter whose key has been rotated, or ask before publishing.
