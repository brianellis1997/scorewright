"""Extract Text2Score's per-measure plan from Brian's Orchestral Idea, in the exact text format the
model was trained on, so bars 1-16 of the plan describe what he actually wrote."""
import os, sys, pickle, warnings
warnings.filterwarnings('ignore')
T2S = '/Users/bdogellis/Documents/Score Exports/_models/_text2score'
sys.path.insert(0, T2S)
from text2music.data.utils.xml2plan import get_full_plan_pipeline, convert_plan_to_text

HERE = os.path.dirname(os.path.abspath(__file__))
XML = '/Users/bdogellis/Documents/Score Exports/MusicXML/Orchestral Idea.musicxml'

plan = get_full_plan_pipeline(XML)
keys = [k for k in plan if k.startswith('Measure')]
print('measures in plan:', len(keys))
print('instruments:', sorted(plan['all_instruments']))
pickle.dump(plan, open(f'{HERE}/oi_plan_full.pkl', 'wb'))

sub = {k: plan[k] for k in keys[:16]}
sub['all_instruments'] = plan['all_instruments']
txt = convert_plan_to_text(sub, plan_length=32)
open(f'{HERE}/oi_plan_1_16.txt', 'w').write(txt)
print(txt)
