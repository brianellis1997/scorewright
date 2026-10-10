#!/bin/sh
# Overnight health watchdog for the combined run. Every 10 min: if the step time has crept past
# 4 s or swap is above 20 GB, restart from the latest periodic checkpoint with a fresh process
# and a new shuffle seed. Logs every decision. Stops when COMBINED_TRAIN_DONE appears.
cd /Users/bdogellis/repos/scorewright/lab
LOG=ft3/rebuild_and_train.log; M="/Users/bdogellis/Documents/Score Exports/_models"; n=0
while true; do
  sleep 600
  awk "/=== /{f=NR} END{print f}" $LOG >/dev/null; tail -n +$(grep -n "=== " $LOG | tail -1 | cut -d: -f1) $LOG | grep -q "COMBINED_TRAIN_DONE" && { echo "$(date +%H:%M) done, watchdog exiting" >> ft3/watchdog.log; exit 0; }
  sit=$(grep -E "^\s+e[0-9] [0-9]+/" $LOG | tail -1 | sed -E 's/.* ([0-9.]+)s\/it.*/\1/')
  swap=$(sysctl vm.swapusage | sed -E 's/.*used = ([0-9.]+)M.*/\1/' | cut -d. -f1)
  alive=$(pgrep -f "ft3/train_edit.py" | wc -l | tr -d ' ')
  echo "$(date +%H:%M) s/it=$sit swap=${swap}M alive=$alive" >> ft3/watchdog.log
  slow=$(echo "$sit > 4.0" | bc 2>/dev/null); [ -z "$slow" ] && slow=0
  if [ "$alive" = "0" ] || [ "$slow" = "1" ] || [ "$swap" -gt 20000 ]; then
    n=$((n+1)); ck="$M/t2s_edit_combined_e1.pth"; [ -f "$ck" ] || ck="$M/t2s_edit_brian_e1.pth"
    echo "$(date +%H:%M) RESTART #$n from $(basename $ck) (slow=$slow swap=$swap alive=$alive)" >> ft3/watchdog.log
    pkill -f "run_combined.sh"; pkill -f "ft3/train_edit.py"; sleep 5
    echo "=== WATCHDOG RESTART #$n $(date +%H:%M) from $(basename $ck)" >> $LOG
    INIT="$ck" PDMX_PER_KIND=1500 T2S_SEED=$n nohup caffeinate -s ./ft3/run_combined.sh >> $LOG 2>&1 &
    sleep 300
  fi
done
