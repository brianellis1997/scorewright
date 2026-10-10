#!/bin/sh
# Waits for the overnight fine-tune, then: stock vs stage 1 vs stage 2, same seam, same plan,
# voice mask + must-play, 2 samples each, verified renders, blind pages.
cd /Users/bdogellis/repos/scorewright/lab
until grep -q "ALL_STAGES_DONE" ft2/train.log 2>/dev/null; do sleep 60; done
P=/Users/bdogellis/miniforge3/envs/text2score/bin/python
W=/Users/bdogellis/miniforge3/envs/whisperer/bin/python
M="/Users/bdogellis/Documents/Score Exports/_models"
export T2S_TOTAL=48 T2S_MINFRAC=0.6
T2S_LABEL=stock_ $P t2s_constrained.py --plan P1_48 --n 2 --temp 1.0
[ -f "$M/weights_text2score_brian.pth" ] && T2S_LABEL=s1_ T2S_CKPT="$M/weights_text2score_brian.pth" $P t2s_constrained.py --plan P1_48 --n 2 --temp 1.0
[ -f "$M/weights_text2score_brian_orch.pth" ] && T2S_LABEL=s2_ T2S_CKPT="$M/weights_text2score_brian_orch.pth" $P t2s_constrained.py --plan P1_48 --n 2 --temp 1.0
TAGS=""
for t in stock_P1_48c_0 stock_P1_48c_1 s1_P1_48c_0 s1_P1_48c_1 s2_P1_48c_0 s2_P1_48c_1; do [ -f "t2s_${t}_final.xml" ] && TAGS="$TAGS $t"; done
$W t2s_blind.py $TAGS
echo MORNING_DONE
