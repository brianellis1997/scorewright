# Preflight before ANY paid run (GPU rental, API spend)

Run every step on the exact code that will train and decode. Paste the outputs into PROJECT.md
under a "preflight" heading BEFORE quoting a cost. If any step is skipped, no spend.

1. Encoded sizes, not characters.
   python ft3/audit_encoded.py <docs.jsonl> 500
   Must print, per task kind: median/max patches, how many docs the trainer would skip
   (answer outside the window), how many answers get cut. Skip rate over 5% for any kind = fix first.

2. Raw decode on the checkpoint you would start from, no harness at all.
   T2S_KINDS=double,continue python ft3/eval_edit.py <eval.jsonl> 3 0.6
   Read the per-doc output lines. If the model stops early, addresses the wrong bar, or emits
   pretraining-format tokens (e.g. [r:i/n]), that is a data-format mismatch: fix the documents,
   do not paper over it at decode time.

3. Same three docs through the decode path the product will actually use (t2s_edit_apply.py),
   rendered, listened to once.

4. One training step on the real trainer with the real config, on 20 docs, on the target
   hardware if possible. Check that the loss covers the answer tokens (print loss_from and the
   decoded target of one batch).

5. Only then: cost = hours x rate + 20% buffer. Write pass/stop criteria that a bar-level
   benchmark can decide. Brian decides.

History: Sept 3-4 2026, $50 GPU day. Steps 1 and 2 were not done. Result: 40-67% of doubling
and fill-harmony documents silently dropped by the character-based crop, and a stopping habit
from pretraining hidden behind the forced decoder. Memory: feedback_no_spend_without_dry_run.
