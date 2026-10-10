#!/bin/sh
# block until Brian says something in the Scorewright surface, then print every line not yet delivered
# (a cursor file keeps the count, so a line written between two waits is never skipped)
Q="/Users/bdogellis/Documents/Score Exports/_bridge/queue/inbox.jsonl"; C="/Users/bdogellis/Documents/Score Exports/_bridge/queue/.inbox_cursor"
touch "$Q"; [ -f "$C" ] || wc -l < "$Q" | tr -d ' ' > "$C"; n=$(cat "$C")
while [ "$(wc -l < "$Q" | tr -d ' ')" -le "$n" ]; do sleep 2; done
tail -n +"$((n+1))" "$Q"; wc -l < "$Q" | tr -d ' ' > "$C"
