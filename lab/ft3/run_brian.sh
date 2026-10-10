#!/bin/sh
cd /Users/bdogellis/repos/scorewright/lab
P=/Users/bdogellis/miniforge3/envs/text2score/bin/python
E="/Users/bdogellis/Documents/Score Exports"
M="$E/_models"
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.8 PYTORCH_MPS_LOW_WATERMARK_RATIO=0.6
export T2S_DOCS="$E/docs_brian.jsonl" T2S_DOCS_EVAL="$E/docs_brian_eval.jsonl" T2S_FREEZE_BELOW=6 T2S_EPOCHS=1 T2S_MAXP=512
INIT="$M/weights_text2score_finetune_p_size_16_p_length_2048_p_layers_20_c_layers_6_h_size_768_lr_0.0001_batch_16.pth"
for e in 1 2; do
  echo "=== EDIT-MODEL epoch $e (his 7,482 docs, eval 1,004)"
  T2S_INIT="$INIT" T2S_OUT="$M/t2s_edit_brian_e$e.pth" $P ft3/train_edit.py
  [ -f "$M/t2s_edit_brian_e$e.pth" ] && INIT="$M/t2s_edit_brian_e$e.pth"
done
echo EDIT_TRAIN_DONE
