#!/bin/bash
cd /workspace/sw && . venv/bin/activate && export SW_ROOT=/workspace/sw PYTHONPATH=/workspace/sw/lab:/workspace/sw/lab/ft3:/workspace/sw/lab/ft2
until grep -q BENCH_POD_DONE bench_cloud_marks.log 2>/dev/null; do sleep 20; done
export T2S_CKPT=/workspace/sw/_models/t2s_edit_cloud.pth T2S_MAXP=2048
T2S_FORCED=1 python lab/ft3/eval_edit.py /workspace/sw/data/docs2_brian_eval.jsonl 20 0.6 > bench3_cloud_edits_forced.log 2>&1
echo BENCH3_POD_DONE >> bench3_cloud_edits_forced.log
T2S_NO_EOS=1 python lab/ft3/eval_edit.py /workspace/sw/data/docs2_brian_eval.jsonl 20 0.6 > bench2_cloud_edits.log 2>&1
T2S_NO_EOS=1 python lab/ft3/eval_edit.py /workspace/sw/data/docs2_marks_brian_eval.jsonl 20 0.6 > bench2_cloud_marks.log 2>&1
echo BENCH2_POD_DONE >> bench2_cloud_marks.log
