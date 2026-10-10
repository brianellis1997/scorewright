#!/bin/sh
export T2S_CKPT='/Users/bdogellis/Documents/Score Exports/_models/cloud/t2s_edit_cloud.pth' T2S_FORCED=1 T2S_TEMP=0.7 T2S_DEVICE=cpu
unset T2S_CUT_AT
/Users/bdogellis/miniforge3/envs/text2score/bin/python t2s_edit_apply.py "/Users/bdogellis/Documents/Score Exports/MusicXML/Mother's Day 2021.musicxml" fill_harmony 29 30 'write the melody in the right hand over the existing bass, bars 29-30' 1 M1_md_fill > apply_M1_md_fill.log 2>&1
/Users/bdogellis/miniforge3/envs/whisperer/bin/python apply_page.py M1_md_fill 29 30 "Mother's Day 2021: model writes the right hand for 29-30 over your bass" >> apply_M1_md_fill.log 2>&1
echo "DONE M1_md_fill" >> mothersday_redo.log
export T2S_CUT_AT=30
/Users/bdogellis/miniforge3/envs/text2score/bin/python t2s_edit_apply.py "/Users/bdogellis/repos/scorewright/lab/apply_M1_md_fill_final.xml" continue 31 38 'continue the piece for 8 more bars' '' M2_md_cont > apply_M2_md_cont.log 2>&1
/Users/bdogellis/miniforge3/envs/whisperer/bin/python apply_page.py M2_md_cont 31 38 "Mother's Day 2021: after filling 29-30, model continues 31-38" >> apply_M2_md_cont.log 2>&1
echo "DONE M2_md_cont" >> mothersday_redo.log
echo BATCH_DONE >> mothersday_redo.log
