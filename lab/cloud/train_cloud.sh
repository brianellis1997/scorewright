#!/bin/bash
# The GPU day. Full context, all layers, every document set, eval every 5K steps, checkpoints.
# Paths assume ~/sw/{lab,data,_models,_text2score}. Env overrides: EPOCHS, LR, ACCUM, MAXP.
set -e
cd ~/sw && . venv/bin/activate
export SW_ROOT=~/sw
D=~/sw/data
cat $D/docs2_multi3.jsonl $D/docs2_marks_pdmx.jsonl $D/docs2_lieder.jsonl $D/docs2_quartets.jsonl $D/docs2_marks_lieder.jsonl $D/docs2_marks_quartets.jsonl \
    $D/docs2_brian.jsonl $D/docs2_brian.jsonl $D/docs2_brian.jsonl $D/docs2_marks_brian.jsonl $D/docs2_marks_brian.jsonl > $D/docs_all.jsonl
python - <<'PY'
import random, json
lines = open('/root/sw/data/docs_all.jsonl').read().splitlines() if __import__('os').path.exists('/root/sw/data/docs_all.jsonl') else open(__import__('os').path.expanduser('~/sw/data/docs_all.jsonl')).read().splitlines()
random.seed(1); random.shuffle(lines)
open(__import__('os').path.expanduser('~/sw/data/docs_all_shuf.jsonl'), 'w').write('\n'.join(lines) + '\n')
print('train docs', len(lines))
PY
export T2S_DOCS=$D/docs_all_shuf.jsonl T2S_DOCS_EVAL=$D/docs2_brian_eval.jsonl
export T2S_MAXP=${MAXP:-2048} T2S_FREEZE_BELOW=0 T2S_EPOCHS=${EPOCHS:-2} T2S_LR=${LR:-5e-5} T2S_ACCUM=${ACCUM:-4}
export T2S_EVAL_EVERY=5000 T2S_EVAL_N=300 T2S_SAVE_EVERY=5000
export T2S_INIT=~/sw/_models/weights_text2score_finetune_p_size_16_p_length_2048_p_layers_20_c_layers_6_h_size_768_lr_0.0001_batch_16.pth
export T2S_OUT=~/sw/_models/t2s_edit_cloud.pth
nohup python ~/sw/lab/ft3/train_edit.py > ~/sw/train_cloud.log 2>&1 &
echo "launched; tail -f ~/sw/train_cloud.log"
