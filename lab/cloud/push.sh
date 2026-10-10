#!/bin/sh
# Upload bundle + run setup on the pod. Logs to cloud/push.log
IP=$(python3 -c "import json;print(json.load(open('$HOME/.config/scorewright/pod_ssh.json'))['ip'])")
PORT=$(python3 -c "import json;print(json.load(open('$HOME/.config/scorewright/pod_ssh.json'))['port'])")
SSH="ssh -o StrictHostKeyChecking=no -o ConnectTimeout=20 -p $PORT root@$IP"
for i in 1 2 3 4 5 6; do $SSH 'echo SSH_OK; nvidia-smi --query-gpu=name,memory.total --format=csv,noheader' && break; echo "ssh retry $i"; sleep 20; done
$SSH 'mkdir -p /workspace/sw && ln -sfn /workspace/sw ~/sw && df -h /workspace | tail -1'
echo "uploading bundle $(date +%H:%M)"
scp -o StrictHostKeyChecking=no -P $PORT /Users/bdogellis/repos/scorewright/lab/sw_bundle.tar root@$IP:/workspace/sw/ && echo "UPLOAD_DONE $(date +%H:%M)"
$SSH 'cd /workspace/sw && tar -xf sw_bundle.tar && rm sw_bundle.tar && ls && du -sh data'
$SSH 'cd /workspace/sw && bash lab/cloud/setup.sh 2>&1 | tail -5'
echo PUSH_DONE
