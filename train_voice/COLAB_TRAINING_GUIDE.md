# 🎙️ Custom Amharic Voice Training & Fine-Tuning Guide
### *Zero-Cost Neural Voice Synthesis Pipeline using Google Colab GPUs & Coqui XTTS-v2*

---

## 📌 Executive Summary

This guide outlines the complete end-to-end workflow for training, fine-tuning, and extracting custom **Amharic speaker embeddings** using open-source deep learning models. By leveraging Google Colab's free cloud GPU tier (NVIDIA T4), you can clone or fine-tune an Amharic voice in under 30 minutes without requiring dedicated local hardware.

---

## 🛠️ Step 1: Dataset Acquisition & Recording

### Option A: Interactive In-Repo Recording Tool (Recommended)
Yakob includes an interactive recording utility configured for 22,050 Hz / 24,000 Hz single-channel PCM audio capture:

```bash
cd train_voice
python prepare_amharic_dataset.py
```
- The prompt engine sequentially displays 20 phonetically balanced Amharic sentences.
- Audio clips are stored in `amharic_dataset/wavs/` and indexed in `amharic_dataset/metadata.csv`.

### Option B: Open-Source Corpora
You may also integrate publicly available open datasets:
- **Mozilla Common Voice (Amharic)**
- **ALFFA Speech Corpus (African Languages Open Data)**

---

## ☁️ Step 2: Google Colab Setup

1. Navigate to [Google Colab](https://colab.research.google.com).
2. Create a new notebook: `File` → `New Notebook`.
3. Switch runtime to GPU acceleration:
   - Navigate to `Runtime` → `Change runtime type`.
   - Select **T4 GPU** under Hardware Accelerator.
   - Click **Save**.

---

## ⚡ Step 3: Execution Script

Run the following code cells in Google Colab:

### Cell 1: Environment Provisioning
```python
# Install Coqui TTS and audio dependencies
!pip install -q coqui-tts soundfile torch
```

### Cell 2: Dataset Ingestion
```python
from google.colab import files
import zipfile
import os

print("Please select and upload your zipped 'amharic_dataset.zip' file:")
uploaded = files.upload()

for filename in uploaded.keys():
    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall('/content/dataset')
print("✅ Dataset successfully extracted.")
```

### Cell 3: Embedding Extraction & Synthesis
```python
import torch
import soundfile as sf
import numpy as np
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

# Initialize Base XTTS-v2 Architecture
print("Fetching pretrained XTTS-v2 model...")
config = XttsConfig()
config.load_json("/root/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2/config.json")

model = Xtts.init_from_config(config)
model.load_checkpoint(config, checkpoint_dir="/root/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2/")
model.cuda()

# Generate conditioning latents and speaker embeddings from sample
reference_audio = "/content/dataset/wavs/am_sample_001.wav"
gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(audio_path=[reference_audio])

# Run validation synthesis in Amharic
test_sentence = "ሰላም! ይህ የእኔ አዲስ የተዘጋጀ የአማርኛ ድምፅ ሞዴል ነው።"
output = model.inference(
    text=test_sentence,
    language="am",
    gpt_cond_latent=gpt_cond_latent,
    speaker_embedding=speaker_embedding,
    temperature=0.65
)

# Export audio verification sample
sf.write("validation_sample.wav", output["wav"], 24000)
print("✅ Validation audio generated successfully.")

# Serialize and download the trained speaker profiles
np.save("yakob_speaker_embedding.npy", speaker_embedding.cpu().numpy())
np.save("yakob_gpt_cond_latent.npy", gpt_cond_latent.cpu().numpy())

files.download("yakob_speaker_embedding.npy")
files.download("yakob_gpt_cond_latent.npy")
files.download("validation_sample.wav")
```

---

## 📥 Step 4: Integration with Yakob Engine

1. Transfer the generated `yakob_speaker_embedding.npy` into the `train_voice/` directory within the Yakob repository.
2. The custom speaker profile is now available for offline neural voice synthesis.
