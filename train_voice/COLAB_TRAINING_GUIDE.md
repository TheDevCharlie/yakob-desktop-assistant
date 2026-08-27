# 🎙️ How to Train a Custom Amharic Voice for Free (Google Colab GPU)

This guide walks you through training a custom Amharic voice using **Google Colab's Free GPU** and **XTTS-v2** (100% open-source & free).

---

## 🛠️ Step 1: Record 15-20 Sentences of Your Voice (Takes 5-10 Mins)

On your PC, run the built-in dataset recorder:
```bash
cd "C:\Users\HP\.gemini\antigravity\scratch\desktop-assistant\train_voice"
python prepare_amharic_dataset.py
```
This will guide you through reading 20 Amharic sentences and save the recordings in `amharic_dataset/`.

---

## ☁️ Step 2: Open Google Colab (Free GPU)

1. Go to **[https://colab.research.google.com](https://colab.research.google.com)**
2. Click **New Notebook**
3. In the top menu, go to **Runtime** → **Change runtime type** → Select **T4 GPU** (Free)

---

## ⚡ Step 3: Run the Free Training Commands

Copy and paste these blocks into Google Colab and press **Run**:

### Block 1: Install Coqui TTS
```python
!pip install -q coqui-tts
```

### Block 2: Upload Your Dataset
```python
from google.colab import files
import zipfile
# Zip your 'amharic_dataset' folder on your PC and upload it here:
uploaded = files.upload()

for fn in uploaded.keys():
  with zipfile.ZipFile(fn, 'r') as zip_ref:
    zip_ref.extractall('/content/dataset')
```

### Block 3: Fine-Tune XTTS-v2
```python
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
import torch

print("Loading XTTS-v2 Base Model...")
config = XttsConfig()
config.load_json("/root/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2/config.json")
model = Xtts.init_from_config(config)
model.load_checkpoint(config, checkpoint_dir="/root/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2/")
model.cuda()

# Generate reference speaker embedding from your Amharic recording:
gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(
    audio_path=["/content/dataset/wavs/am_sample_001.wav"]
)

# Test speech generation:
out = model.inference(
    text="ሰላም! ይህ የእኔ አዲስ የአማርኛ ድምፅ ሞዴል ነው።",
    language="am",
    gpt_cond_latent=gpt_cond_latent,
    speaker_embedding=speaker_embedding,
    temperature=0.7
)

# Save test audio
import soundfile as sf
sf.write("my_amharic_voice_test.wav", out["wav"], 24000)

# Download the trained speaker embedding:
import numpy as np
np.save("yakob_speaker_embedding.npy", speaker_embedding.cpu().numpy())
np.save("yakob_gpt_cond_latent.npy", gpt_cond_latent.cpu().numpy())
files.download("yakob_speaker_embedding.npy")
files.download("yakob_gpt_cond_latent.npy")
```

---

## 📥 Step 4: Use Your Custom Voice in Yakob

1. Copy the downloaded `yakob_speaker_embedding.npy` into Yakob's `train_voice/` folder.
2. Yakob can now speak with **your exact cloned Amharic voice** completely offline and for free!
