#!/bin/sh
# Every 10 minutes: pull the training log and every checkpoint from the pod to the Mac, and
# record spend. Nothing that happens on the box stays only on the box.
DST="/Users/bdogellis/Documents/Score Exports/_models/cloud"
IP=$(python3 -c "import json;print(json.load(open('$HOME/.config/scorewright/pod_ssh.json'))['ip'])")
PORT=$(python3 -c "import json;print(json.load(open('$HOME/.config/scorewright/pod_ssh.json'))['port'])")
while true; do
  scp -q -o StrictHostKeyChecking=no -o ConnectTimeout=20 -P $PORT root@$IP:/workspace/sw/train_cloud.log "$DST/train_cloud.log" 2>/dev/null
  rsync -az -e "ssh -o StrictHostKeyChecking=no -p $PORT" --include='*.pth' --exclude='*' root@$IP:/workspace/sw/_models/ "$DST/" 2>/dev/null
  set -a; . $HOME/.config/scorewright/runpod.env; set +a
  bal=$(curl -s -H "Authorization: Bearer $RUNPOD_API_KEY" -H "Content-Type: application/json" -X POST https://api.runpod.io/graphql -d '{"query":"query { myself { clientBalance } }"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['myself']['clientBalance'])" 2>/dev/null)
  echo "$(date '+%m-%d %H:%M') balance \$$bal | $(grep -E 'EVAL@|EPOCH' "$DST/train_cloud.log" 2>/dev/null | tail -1)" >> "$DST/sync.log"
  grep -q "TRAINING DONE" "$DST/train_cloud.log" 2>/dev/null && { echo "$(date '+%m-%d %H:%M') training done, final sync" >> "$DST/sync.log"; sleep 60; rsync -az -e "ssh -o StrictHostKeyChecking=no -p $PORT" --include='*.pth' --exclude='*' root@$IP:/workspace/sw/_models/ "$DST/"; exit 0; }
  sleep 600
done
