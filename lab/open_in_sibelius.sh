#!/bin/sh
# open a MusicXML in Sibelius and accept its import dialog automatically
open -a Sibelius "$1"; sleep 4
osascript -e 'tell application "System Events" to tell process "Sibelius" to keystroke return' >/dev/null 2>&1
echo "opened in Sibelius: $1"
