from faster_whisper import WhisperModel

LANG = "ar,en"
model = WhisperModel("small", device="cpu")
audio = "myvoice.wav"

segments, _ = model.transcribe(audio, language=LANG, vad_filter=True, word_timestamps=True)
print("📋 الكلمات المكتشفة:")
for seg in segments:
    for w in seg.words or []:
        print(f"{w.word.strip()}  [{w.start:.2f}s -> {w.end:.2f}s]")
