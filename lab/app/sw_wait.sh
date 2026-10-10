#!/bin/sh
# block until Brian says something in the Scorewright surface, then print every line not yet delivered
# (a cursor file keeps the count, so a line written between two waits is never skipped)
Q="/Users/bdogellis/Documents/Score Exports/_bridge/queue/inbox.jsonl"; C="/Users/bdogellis/Documents/Score Exports/_bridge/queue/.inbox_cursor"
L="/Users/bdogellis/Documents/Score Exports/_bridge/queue/.listener"   # heartbeat: the page shows whether Claude is listening
touch "$Q"; [ -f "$C" ] || wc -l < "$Q" | tr -d ' ' > "$C"; n=$(cat "$C"); date +%s > "$L"
while [ "$(wc -l < "$Q" | tr -d ' ')" -le "$n" ]; do sleep 2; date +%s > "$L"; done
tail -n +"$((n+1))" "$Q"; wc -l < "$Q" | tr -d ' ' > "$C"
