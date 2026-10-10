#!/bin/sh
# Combined instructed-infill run: PDMX multi3 (capped) + OpenScore + Brian, one process per epoch.
# Brian's docs are repeated 3x so his voice is not drowned by PDMX (about 8K vs 180K).
cd /Users/bdogellis/repos/scorewright/lab
P=/Users/bdogellis/miniforge3/envs/text2score/bin/python
E="/Users/bdogellis/Documents/Score Exports"; C="$E/_corpora"; M="$E/_models"
PDMX_PER_KIND="${PDMX_PER_KIND:-2500}"
$P - "$C/pdmx/v2/${DP:-docs}_multi3.jsonl" "$E/docs_pdmx_sample.jsonl" "$PDMX_PER_KIND" <<'PY'
import sys, json, random, collections
src, dst, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
random.seed(5); by = collections.defaultdict(list)
for l in open(src):
    k = json.loads(l)['kind']; by[k].append(l)
with open(dst, 'w') as f:
    for k, ls in by.items():
        random.shuffle(ls); f.writelines(ls[:n])
print('pdmx sample', {k: min(n, len(v)) for k, v in by.items()})
PY
cat "$E/docs_pdmx_sample.jsonl" "$C/openscore_xml/${DP:-docs}_lieder.jsonl" "$C/openscore_xml/${DP:-docs}_quartets.jsonl" "$E/${DP:-docs}_brian.jsonl" "$E/${DP:-docs}_brian.jsonl" > "$E/docs_combined.jsonl"
cat "$C/pdmx/v2/${DP:-docs}_multi3_eval.jsonl" "$C/openscore_xml/${DP:-docs}_lieder_eval.jsonl" "$C/openscore_xml/${DP:-docs}_quartets_eval.jsonl" "$E/${DP:-docs}_brian_eval.jsonl" > "$E/docs_combined_eval.jsonl"
echo "combined train $(wc -l < "$E/docs_combined.jsonl") eval $(wc -l < "$E/docs_combined_eval.jsonl")"
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.8 PYTORCH_MPS_LOW_WATERMARK_RATIO=0.6
export T2S_DOCS="$E/docs_combined.jsonl" T2S_DOCS_EVAL="$E/${DP:-docs}_brian_eval.jsonl" T2S_FREEZE_BELOW=6 T2S_EPOCHS=1 T2S_MAXP=512
INIT="${INIT:-$M/weights_text2score_finetune_p_size_16_p_length_2048_p_layers_20_c_layers_6_h_size_768_lr_0.0001_batch_16.pth}"
for e in 1 2; do
  echo "=== COMBINED epoch $e"
  T2S_INIT="$INIT" T2S_OUT="$M/t2s_edit_${DP:-docs}_e$e.pth" $P ft3/train_edit.py
  [ -f "$M/t2s_edit_${DP:-docs}_e$e.pth" ] && INIT="$M/t2s_edit_${DP:-docs}_e$e.pth"
done
echo COMBINED_TRAIN_DONE
