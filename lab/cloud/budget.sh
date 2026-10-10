#!/bin/sh
# Hard stop: terminate the pod when balance <= $10 (= $50 spent), after 14.5 h, or once training
# is done and the final sync has had a minute. Checks every 5 minutes. Logs to cloud/budget.log
START=$(date +%s); DST="/Users/bdogellis/Documents/Score Exports/_models/cloud"
set -a; . $HOME/.config/scorewright/runpod.env; set +a
PID=$(python3 -c "import json;print(json.load(open('$HOME/.config/scorewright/pod_ssh.json'))['id'])")
stop_pod() { curl -s -H "Authorization: Bearer $RUNPOD_API_KEY" -H "Content-Type: application/json" -X POST https://api.runpod.io/graphql -d "{\"query\":\"mutation { podTerminate(input:{podId:\\\"$PID\\\"}) }\"}"; echo " $(date '+%m-%d %H:%M') POD TERMINATED ($1)" >> cloud/budget.log; }
while true; do
  bal=$(curl -s -H "Authorization: Bearer $RUNPOD_API_KEY" -H "Content-Type: application/json" -X POST https://api.runpod.io/graphql -d '{"query":"query { myself { clientBalance } }"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['myself']['clientBalance'])" 2>/dev/null)
  hours=$(( ($(date +%s) - START) / 3600 ))
  echo "$(date '+%m-%d %H:%M') balance=\$$bal elapsed=${hours}h" >> cloud/budget.log
  low=$(python3 -c "print(1 if float('${bal:-99}') <= 10 else 0)")
  if [ "$low" = "1" ]; then stop_pod "balance"; exit 0; fi
  if [ $(( $(date +%s) - START )) -ge 52200 ]; then stop_pod "14.5h"; exit 0; fi
  if grep -q "TRAINING DONE" "$DST/train_cloud.log" 2>/dev/null; then sleep 900; stop_pod "training done"; exit 0; fi
  sleep 300
done
