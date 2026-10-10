#!/bin/sh
export T2S_CKPT='/Users/bdogellis/Documents/Score Exports/_models/cloud/t2s_edit_cloud.pth' T2S_FORCED=1 T2S_TEMP=0.7 T2S_DEVICE=cpu
run() { tag=$1; xml=$2; last=$3; title=$4; lo=$((last+1)); hi=$((last+8))
  export T2S_CUT_AT=$last
  /Users/bdogellis/miniforge3/envs/text2score/bin/python t2s_edit_apply.py "$xml" continue $lo $hi 'continue the piece for 8 more bars' '' $tag > apply_$tag.log 2>&1
  /Users/bdogellis/miniforge3/envs/whisperer/bin/python apply_page.py $tag $lo $hi "$title" >> apply_$tag.log 2>&1
  echo "DONE $tag" >> unfinished_batch.log; }
run U1_35piano "/Users/bdogellis/Documents/Score Exports/MusicXML/3 5 piano.musicxml" 35 '3 5 piano (Jul 2021, unfinished at bar 35): model writes 36-43'
run U2_420piano "/Users/bdogellis/Documents/Score Exports/MusicXML/4 20 piano.musicxml" 35 '4 20 piano (Apr 2021, unfinished at bar 35): model writes 36-43'
run U3_mothersday "/Users/bdogellis/Documents/Score Exports/MusicXML/Mother's Day 2021.musicxml" 30 "Mother's Day 2021 (unfinished at bar 30): model writes 31-38"
run U4_724piano "/Users/bdogellis/Documents/Score Exports/MusicXML/724 piano.musicxml" 22 '724 piano (Jul 2020, unfinished at bar 22): model writes 23-30'
run U5_lonesome "/Users/bdogellis/Documents/Score Exports/MusicXML/630 piano lonesome theme.musicxml" 41 '630 piano lonesome theme (Jul 2020, unfinished at bar 41): model writes 42-49'
run U6_brightvalley "/Users/bdogellis/Documents/Score Exports/MusicXML/Bright Valley Exaltation Sketch.musicxml" 95 'Bright Valley Exaltation Sketch (Apr 2021, unfinished at bar 95): model writes 96-103'
echo BATCH_DONE >> unfinished_batch.log
