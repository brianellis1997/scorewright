#!/bin/sh
# One epoch per process. The MPS allocator grows across epochs on this 16GB machine (2.3 s/step
# in epoch 1, 9.4 s/step by epoch 3, with 5.7GB in the compressor); a fresh process gets the
# speed back, exactly as the NotaGen run showed. Each epoch saves to its own file; the best eval
# wins at the end. Appends to ft2/train.log so the monitor and t2s_morning.sh keep working.
cd /Users/bdogellis/repos/scorewright/lab
P=/Users/bdogellis/miniforge3/envs/text2score/bin/python
M="/Users/bdogellis/Documents/Score Exports/_models"
LOG=ft2/train.log
best_of() {   # best_of <out> <cand...> : copy the candidate with the lowest eval to <out>
  $P - "$@" <<'EOF'
import sys, shutil, torch
out, cands = sys.argv[1], sys.argv[2:]
best = None
for c in cands:
    try:
        ev = torch.load(c, map_location='cpu', weights_only=False).get('eval', 9e9)
    except Exception:
        continue
    print(f'  {c.split("/")[-1]}: eval {ev:.4f}', flush=True)
    if best is None or ev < best[0]:
        best = (ev, c)
if best:
    shutil.copy(best[1], out); print(f'  BEST -> {out.split("/")[-1]} (eval {best[0]:.4f})', flush=True)
EOF
}

echo "=== STAGE 1 (continued, one process per epoch): epochs 4-6 from the epoch-3 checkpoint" >> $LOG
INIT="$M/weights_text2score_brian.pth"
for e in 4 5 6; do
  T2S_MIN_INST=3 T2S_FREEZE_BELOW=6 T2S_EPOCHS=1 T2S_MAXP=512 T2S_INIT="$INIT" T2S_OUT="$M/t2s_s1_e$e.pth" $P ft2/train_t2s.py >> $LOG 2>&1
  [ -f "$M/t2s_s1_e$e.pth" ] && INIT="$M/t2s_s1_e$e.pth"
done
best_of "$M/weights_text2score_brian.pth" "$M/weights_text2score_brian.pth" "$M/t2s_s1_e4.pth" "$M/t2s_s1_e5.pth" "$M/t2s_s1_e6.pth" >> $LOG 2>&1

echo "=== STAGE 2: >=6 instruments, 768-patch crops, 4 epochs, one process per epoch, from stage-1 best" >> $LOG
INIT="$M/weights_text2score_brian.pth"
for e in 1 2 3 4; do
  T2S_MIN_INST=6 T2S_FREEZE_BELOW=6 T2S_EPOCHS=1 T2S_MAXP=768 T2S_INIT="$INIT" T2S_OUT="$M/t2s_s2_e$e.pth" $P ft2/train_t2s.py >> $LOG 2>&1
  [ -f "$M/t2s_s2_e$e.pth" ] && INIT="$M/t2s_s2_e$e.pth"
done
best_of "$M/weights_text2score_brian_orch.pth" "$M/t2s_s2_e1.pth" "$M/t2s_s2_e2.pth" "$M/t2s_s2_e3.pth" "$M/t2s_s2_e4.pth" >> $LOG 2>&1
echo ALL_STAGES_DONE >> $LOG
