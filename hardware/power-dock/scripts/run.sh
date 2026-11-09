#!/bin/sh
# Regenerate schematic + board with KiCad's bundled Python (pcbnew module).
APPDIR=${KICAD_APPDIR:-/opt/data/cache/kicad/AppDir}
export PYTHONPATH=$APPDIR/shared/lib/python3.11/dist-packages
export LD_LIBRARY_PATH=$APPDIR/usr/lib:$APPDIR/usr/lib/x86_64-linux-gnu
export KISHARE=$APPDIR/usr/share/kicad
exec "$APPDIR/usr/bin/python3.11" "${SCRIPT:-$(dirname "$0")/build.py}" "$@"
