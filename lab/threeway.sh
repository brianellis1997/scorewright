#!/bin/sh
until grep -q "CHAIN_DONE\|KILLED" docs3_cpu.log 2>/dev/null; do sleep 30; done
export T2S_TEMP=0.7 T2S_DEVICE=cpu T2S_STREAM=1
run() { tag=$1; xml=$2; last=$3; title=$4; ckpt=$5; forced=$6; lo=$((last+1)); hi=$((last+8))
  export T2S_CUT_AT=$last
  if [ -n "$ckpt" ]; then export T2S_CKPT="$ckpt"; else unset T2S_CKPT; fi
  if [ -n "$forced" ]; then export T2S_FORCED=1; else unset T2S_FORCED; fi
  nice -n 15 /Users/bdogellis/miniforge3/envs/text2score/bin/python t2s_edit_apply.py "$xml" continue $lo $hi 'continue the piece for 8 more bars, both hands' '' $tag > apply_$tag.log 2>&1
  /Users/bdogellis/miniforge3/envs/whisperer/bin/python apply_page.py $tag $lo $hi "$title" >> apply_$tag.log 2>&1
  echo "DONE $tag" >> threeway.log; }
run T1_35_stock "/Users/bdogellis/Documents/Score Exports/MusicXML/3 5 piano.musicxml" 35 "3 5 piano: ORIGINAL NotaGen/Text2Score weights, native format, bars 36-43" "" 1
run T2_35_native "/Users/bdogellis/Documents/Score Exports/MusicXML/3 5 piano.musicxml" 35 "3 5 piano: retrained 300 steps in native format, bars 36-43" "/Users/bdogellis/Documents/Score Exports/_models/t2s_docs3_cpu300.pth" 1
run T3_35_native_raw "/Users/bdogellis/Documents/Score Exports/MusicXML/3 5 piano.musicxml" 35 "3 5 piano: retrained in native format, RAW (no scaffolding), bars 36-43" "/Users/bdogellis/Documents/Score Exports/_models/t2s_docs3_cpu300.pth" ""
run T4_724_stock "/Users/bdogellis/Documents/Score Exports/MusicXML/724 piano.musicxml" 22 "724 piano: ORIGINAL weights, native format, bars 23-30" "" 1
run T5_724_native "/Users/bdogellis/Documents/Score Exports/MusicXML/724 piano.musicxml" 22 "724 piano: retrained 300 steps in native format, bars 23-30" "/Users/bdogellis/Documents/Score Exports/_models/t2s_docs3_cpu300.pth" 1
echo BATCH_DONE >> threeway.log
