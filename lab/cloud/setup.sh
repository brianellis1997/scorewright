#!/bin/bash
# One-time setup on a fresh Linux GPU box (Ubuntu, CUDA driver present). Run from ~/sw.
set -e
cd ~/sw
python3 -m venv venv && . venv/bin/activate
pip install -q --upgrade pip
pip install -q torch --index-url https://download.pytorch.org/whl/cu124
pip install -q "transformers>=4.48" accelerate samplings unidecode numpy scipy tqdm
git clone -q https://github.com/keshavbhandari/text2score.git _text2score
mkdir -p _models && cd _models
curl -sL -o weights_text2score_finetune_p_size_16_p_length_2048_p_layers_20_c_layers_6_h_size_768_lr_0.0001_batch_16.pth \
  "https://huggingface.co/keshavbhandari/Text2Score/resolve/main/weights_text2score_finetune_p_size_16_p_length_2048_p_layers_20_c_layers_6_h_size_768_lr_0.0001_batch_16.pth"
cd ~/sw && python - <<'PY'
from transformers import AutoTokenizer, AutoModelForMaskedLM
AutoTokenizer.from_pretrained('answerdotai/ModernBERT-base'); AutoModelForMaskedLM.from_pretrained('answerdotai/ModernBERT-base')
print('ModernBERT cached')
PY
nvidia-smi --query-gpu=name,memory.total --format=csv
echo SETUP_DONE
