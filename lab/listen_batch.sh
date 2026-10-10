#!/bin/sh
export T2S_CKPT='/Users/bdogellis/Documents/Score Exports/_models/cloud/t2s_edit_cloud.pth' T2S_FORCED=1 T2S_TEMP=0.7
run() { tag=$1; xml=$2; kind=$3; lo=$4; hi=$5; instr=$6; voice=$7; title=$8; cut=$9
  if [ -n "$cut" ]; then export T2S_CUT_AT=$cut; else unset T2S_CUT_AT; fi
  /Users/bdogellis/miniforge3/envs/text2score/bin/python t2s_edit_apply.py "$xml" $kind $lo $hi "$instr" "$voice" $tag > apply_$tag.log 2>&1
  /Users/bdogellis/miniforge3/envs/whisperer/bin/python apply_page.py $tag $lo $hi "$title" >> apply_$tag.log 2>&1
  echo "DONE $tag" >> listen_batch.log; }
run L1_impr "/Users/bdogellis/Documents/Score Exports/MusicXML/Impressionistic Piece no 4.musicxml" continue 41 48 'continue the piece for 8 more bars' '' 'Impressionistic Piece no 4: model writes 41-48 (yours from 49)' 40
run L2_seren "/Users/bdogellis/Documents/Score Exports/MusicXML/Serenade in E.musicxml" continue 33 40 'continue the piece for 8 more bars' '' 'Serenade in E: model writes 33-40 (yours from 41)' 32
run L3_no3 "/Users/bdogellis/Documents/Score Exports/MusicXML/No 3 in C.musicxml" continue 25 32 'continue the piece for 8 more bars' '' 'No 3 in C: model writes 25-32 (yours from 33)' 24
run L4_briello "/Users/bdogellis/Documents/Score Exports/MusicXML/Briello no 329.musicxml" continue 21 28 'continue the piece for 8 more bars' '' 'Briello no 329: model writes 21-28 (yours from 29)' 20
run L5_sonata "/Users/bdogellis/Documents/Score Exports/MusicXML/Piano Sonata in Gm BEM 001.musicxml" fill_harmony 61 64 'fill in the harmony in the left hand, bars 61-64' 2 'Piano Sonata in Gm: model fills the left hand 61-64' ''
run L6_impr_fill "/Users/bdogellis/Documents/Score Exports/MusicXML/Impressionistic Piece no 4.musicxml" fill_harmony 80 83 'fill in the harmony in the left hand, bars 80-83' 2 'Impressionistic Piece no 4: model fills the left hand 80-83' ''
echo BATCH_DONE >> listen_batch.log
