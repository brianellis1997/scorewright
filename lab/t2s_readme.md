# Text2Score

GitHub repo for Text2Score: Generating Sheet Music From Textual Prompts

[![Demo](https://img.shields.io/badge/Demo-Live-brightgreen)](https://keshavbhandari.github.io/portfolio/text2score)
[![Dataset](https://img.shields.io/badge/Dataset-HuggingFace-yellow)](https://huggingface.co/datasets/emotionwave-company/text2score)
[![Paper](https://img.shields.io/badge/Paper-Arxiv-red)](https://arxiv.org/abs/2605.13431)
[![Model Weights](https://img.shields.io/badge/Model-HuggingFace-orange)](https://huggingface.co/keshavbhandari/Text2Score)

**Note on Model Weights:** The pre-trained and fine-tuned model checkpoints are hosted on [Hugging Face](https://huggingface.co/keshavbhandari/Text2Score). You do not need to download these manually; the inference scripts are configured to automatically download the weights the first time you run them.

## System Overview
For a high-level view of the model architecture and pipeline, please see the system overview below:

![System Overview](text2music/artifacts/system_overview.png)

---

## Installation

**1. Clone the repository**
```bash
git clone https://github.com/keshavbhandari/text2score.git
cd text2score
```

**2. Create and activate a new Conda environment**
```bash
conda create --name text2score python=3.10
conda activate text2score
```

**3. Install PyTorch with CUDA support**
```bash
conda install pytorch=2.3.0 pytorch-cuda=11.8 numpy -c pytorch -c nvidia
```

**4. Install the project and dependencies**
Ensure you are in the root directory (where `pyproject.toml` is located) and run:
```bash
pip install -e .
pip install optimum
```

---

## Inference & Usage

All scripts should be executed from within the root `text2score` directory. 

### 1. Generating Plans from Prompts
Before running batch inference, you can generate execution plans based on a JSON of prompts.
```bash
python text2music/inference/generate_plan.py \
  --api_key "XXXX" \
  --input_json text2music/artifacts/evaluation/prompts_with_ids.json \
  --output_json text2music/artifacts/evaluation/prompts_with_plan.json
```

**Note:** You will need an active OpenAI API key to run this script as it uses the API to generate the plans. The script currently defaults to using the `GPT-5.1` model for plan generation, but you can easily modify the script to use any other supported model.

### 2. Batch Inference
Run inference across multiple prompts. Run step 1 to have your prompts and corresponding plans in a JSON file (see `text2music/artifacts/evaluation/prompts/prompts_with_plan.json` for an example of the expected format). Then execute:
```bash
accelerate launch --num_processes 1 text2music/inference/run_inference.py \
  --prompt_path_json text2music/artifacts/evaluation/prompts_with_plan.json \
  --output_folder text2music/artifacts/outputs/
```

### 3. Single Inference
To generate a score from a single text prompt:
```bash
python text2music/inference/inference.py \
  --user_prompt "A melancholic solo flute melody settling back into D minor, composed as a slow 6/8 barcarolle at 54 BPM." \
  --api_key "XXXX" \
  --remove_prior_outputs False
```

**Note:** You will need an active OpenAI API key to run the script this way, as it automatically generates the necessary execution plans on the fly. The script currently defaults to using the `GPT-5.1` model for plan generation, but you can easily modify the script to use any other supported model.

Or if you don't want to use the API and already have a pre-generated plan text file (see note below), use:
```bash
python text2music/inference/inference.py \
  --plan_path text2music/artifacts/example_plans/partial_plan.txt \
  --remove_prior_outputs False
```

*Tip: If you prefer to generate a plan manually, you can copy the system prompt found in `text2score/text2music/inference/prompt.py` (add your own prompt in the placeholder text) and paste it into the interface for ChatGPT, Gemini, or any other LLM of your choice along with your desired music prompt. Simply take the LLM's output, replace the contents of `text2score/text2music/artifacts/example_plans/partial_plan.txt` entirely with that new plan, and run the command above.*

---

## Data Conversion (ABC to XML & MIDI)

Once you have generated ABC files, you can batch convert them into standard XML and MIDI formats.

**Create XML files:**
```bash
python text2music/data/batch_abci2xml.py --root_folder text2music/artifacts/
```

**Create MIDI files:**
```bash
python text2music/data/utils/xml2mid.py --data_dir text2music/artifacts/
```

---

## Evaluation

To evaluate the generated objective results against your metadata:
```bash
python text2music/scripts/evaluation.py \
  --root text2music/artifacts/outputs/ \
  --metadata text2music/artifacts/evaluation/prompts_with_plan.json \
  --output_txt text2music/scripts/results/text2score_objective_results.txt
```

---

## Training

Ensure your `accelerate` configs are initialized and that your train/validation `.jsonl` files contain the correct paths to your `.abci` and `.pkl` files.

**Run Pretraining:**
```bash
accelerate launch --num_processes 2 text2music/pretrain/train-gen.py
```

**Run Fine-tuning:**
```bash
accelerate launch --num_processes 2 text2music/finetune/train-gen.py
```

## Citation

If you find this repository useful in your research, please consider citing our work:

```bibtex
@article{bhandari2025text2score,
  title     = {Text2Score: Generating Sheet Music from Textual Prompts},
  author    = {Bhandari, Keshav and Chang, Sungkyun and Roy, Abhinaba and Ronchini, Francesca and Benetos, Emmanouil and Herremans, Dorien and Colton, Simon},
  journal   = {arXiv preprint arXiv:2605.13431},
  year      = {2026},
  url       = {https://arxiv.org/abs/2605.13431}
}
```