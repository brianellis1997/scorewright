#!/bin/sh
# block until Brian says something in the Scorewright surface, then print every line not yet delivered
# (a cursor file keeps the count, so a line written between two waits is never skipped).
# An Accept of a suggestion with a Dorico plan goes into his Dorico project right here (sw_on_accept.py),
# before Claude reads the lines.
Q="/Users/bdogellis/Documents/Score Exports/_bridge/queue/inbox.jsonl"; C="/Users/bdogellis/Documents/Score Exports/_bridge/queue/.inbox_cursor"
L="/Users/bdogellis/Documents/Score Exports/_bridge/queue/.listener"   # heartbeat: the page shows whether Claude is listening
touch "$Q"; [ -f "$C" ] || wc -l < "$Q" | tr -d ' ' > "$C"; n=$(cat "$C"); date +%s > "$L"
while [ "$(wc -l < "$Q" | tr -d ' ')" -le "$n" ]; do sleep 1; date +%s > "$L"; done
NEW=$(tail -n +"$((n+1))" "$Q"); wc -l < "$Q" | tr -d ' ' > "$C"
printf '%s\n' "$NEW" | /Users/bdogellis/miniforge3/envs/whisperer/bin/python /Users/bdogellis/repos/scorewright/lab/app/sw_on_accept.py
printf '%s\n' "$NEW"
