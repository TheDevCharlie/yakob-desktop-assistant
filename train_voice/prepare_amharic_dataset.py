"""
Amharic Voice Dataset Recorder & Formatter (100% Free).
Lets you record or format short Amharic sentences to train your custom voice model.
"""
import os
import sys
import time
from pathlib import Path
import sounddevice as sd
import soundfile as sf

# 30 Sample Sentences in Amharic for Voice Training
TRAINING_PROMPTS = [
    "ሰላም እንደምን አደሩ! ዛሬ መልካም እና የተባረከ ቀን ይሁንልዎ።",
    "እኔ ያዕቆብ እባላለሁ፤ የእርስዎ የኮምፒውተር ድምፅ ረዳት ነኝ።",
    "የኢትዮጵያ ታሪክ እጅግ ጥንታዊ፣ ሰፊና አስደናቂ ባህል ያለው ነው።",
    "በዓለም ላይ ከሰባት ሺህ በላይ ቋንቋዎች በሰው ልጆች ይነገራሉ።",
    "ኮምፒውተርዎን በድምፅ ትእዛዝ ብቻ በቀላሉ ማዘዝ ይችላሉ።",
    "የአየር ሁኔታው ዛሬ በጣም ፀሐያማና አስደሳች ነው።",
    "ትዕግሥት መራራ ናት፤ ፍሬዋ ግን እጅግ ጣፋጭ ነው።",
    "የአንድ ሺህ ማይል ጉዞ በአንዲት ትንሽ እርምጃ ይጀምራል።",
    "አዲስ አበባ የኢትዮጵያ ዋና ከተማና የዲፕሎማሲ ማዕከል ናት።",
    "የአባይ ወንዝ ከጣና ሐይቅ ተነስቶ ረጅም ጉዞ ያደርጋል።",
    "የዓድዋ ድል ለአፍሪካውያን በሙሉ የታላቅነትና የነፃነት ምልክት ነው።",
    "ሳይንስና ቴክኖሎጂ የሰውን ልጅ ኑሮ በእጅጉ እያቀላጠፉ ይገኛሉ።",
    "ለማንኛውም ጥያቄ ወይም እርዳታ ሁልጊዜ ዝግጁ ሆኜ እጠብቃለሁ።",
    "የጠዋት ንጹህ አየር ለአእምሮና ለአካል ጤና በጣም ጠቃሚ ነው።",
    "የሚፈልጉትን መተግበሪያ በቅጽበት ለመክፈት ትእዛዝዎን ይስጡኝ።",
    "እውቀት ማንም ሊሰርቀው የማይችል ታላቅ የህይወት ሀብት ነው።",
    "ዛሬ የጀመርከው ጥረት የነገው ስኬትህ ጽኑ መሰረት ይሆናል።",
    "በስርዓተ-ፀሐይ ውስጥ ስምንት ፕላኔቶች በፀሐይ ዙሪያ ይሽከረከራሉ።",
    "የተፈጥሮ ውበትና አረንጓዴ አካባቢ መንፈስን ያድሳል።",
    "የድምፅ ረዳት ቴክኖሎጂ የዕለት ተዕለት ስራዎችን ፈጣን ያደርጋል።"
]


def record_training_dataset(output_dir: str = "./amharic_dataset"):
    dataset_path = Path(output_dir)
    wavs_path = dataset_path / "wavs"
    wavs_path.mkdir(parents=True, exist_ok=True)

    metadata_file = dataset_path / "metadata.csv"
    sample_rate = 22050

    print("=" * 70)
    print("🎙️ AMHARIC VOICE DATASET RECORDING TOOL (FREE)")
    print(f"   Destination: {dataset_path.resolve()}")
    print("   Press ENTER to start recording each sentence, speak, then press ENTER again.")
    print("=" * 70)

    records = []

    for idx, prompt in enumerate(TRAINING_PROMPTS, 1):
        filename = f"am_sample_{idx:03d}.wav"
        filepath = wavs_path / filename

        print(f"\n[{idx}/{len(TRAINING_PROMPTS)}] Please read this sentence aloud in Amharic:")
        print(f"👉 \"{prompt}\"")
        input("Press [ENTER] when ready to start recording...")

        print("🔴 Recording... Speak now!")
        recorded_chunks = []
        is_recording = True

        def callback(indata, frames, time_info, status):
            if is_recording:
                recorded_chunks.append(indata.copy())

        stream = sd.InputStream(samplerate=sample_rate, channels=1, dtype='float32', callback=callback)
        with stream:
            input("Press [ENTER] to STOP recording...")
            is_recording = False

        if recorded_chunks:
            import numpy as np
            audio_data = np.concatenate(recorded_chunks, axis=0)
            audio_int16 = (np.clip(audio_data, -1.0, 1.0) * 32767).astype(np.int16)
            sf.write(str(filepath), audio_int16, sample_rate)
            records.append(f"{filename}|{prompt}")
            print(f"✅ Saved: {filename} ({len(audio_data)/sample_rate:.1f}s)")

    with open(metadata_file, "w", encoding="utf-8") as f:
        f.write("\n".join(records))

    print("\n" + "=" * 70)
    print(f"🎉 Dataset recording complete! Files saved in: {dataset_path.resolve()}")
    print("   Upload this folder to Google Colab to train your free custom voice model.")
    print("=" * 70)


if __name__ == "__main__":
    record_training_dataset()
