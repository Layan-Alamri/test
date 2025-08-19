# censor.py
# يشفر الكلمات السيئة (من القائمة) بـ "بيب"
import re, math, wave, numpy as np
from faster_whisper import WhisperModel

# إعدادات
LANG = "ar,en"          # عربي + إنجليزي
WHISPER_SIZE = "small"  # غيّريها tiny/base/medium حسب جهازك
BEEP_FREQ = 1000        # Hz
PAD_MS = 50             # هامش قبل/بعد الكلمة
SR_TARGET = 16000       # تردد الصوت

# الكلمات المسيئة فقط (زي ما طلبتِ)
BAD_WORDS = ["حيوان", "زق", "غبي", "idiot", "stupid", "shit"]
bad_re = re.compile("|".join([fr"\b{w}\b" for w in BAD_WORDS]), flags=re.IGNORECASE)

def normalize_ar(text: str) -> str:
    text = re.sub(r"[\u0617-\u061A\u064B-\u0652]", "", text)
    text = re.sub(r"[ـ]", "", text)
    text = re.sub(r"[إأآا]", "ا", text)
    text = re.sub(r"ى", "ي", text)
    text = re.sub(r"ؤ", "و", text)
    text = re.sub(r"ئ", "ي", text)
    return text.strip().lower()

def transcribe(audio_path: str):
    model = WhisperModel(WHISPER_SIZE, device="cpu")
    segments, _ = model.transcribe(audio_path, language=LANG, vad_filter=True, word_timestamps=True)
    words = []
    for seg in segments:
        for w in seg.words or []:
            words.append((w.word.strip(), float(w.start), float(w.end)))
    return words

def find_bad_spans(words):
    spans = []
    for w, s, e in words:
        if bad_re.search(normalize_ar(w)):
            spans.append((s, e))
    return spans

def load_wav(path):
    with wave.open(path, "rb") as wf:
        ch, sw, fr, nframes = wf.getnchannels(), wf.getsampwidth(), wf.getframerate(), wf.getnframes()
        raw = wf.readframes(nframes)
    assert sw == 2, "الملف لازم يكون 16-bit PCM"
    data = np.frombuffer(raw, dtype="<i2").astype(np.int16)
    if ch > 1:
        data = data.reshape(-1, ch).mean(axis=1).astype(np.int16)
    return data, fr

def save_wav(path, data, fr):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(fr)
        wf.writeframes(data.astype("<i2").tobytes())

def resample(x, sr_from, sr_to):
    if sr_from == sr_to: return x, sr_from
    t_old = np.linspace(0, len(x)/sr_from, num=len(x), endpoint=False)
    t_new = np.linspace(0, len(x)/sr_to,   num=int(len(x)*sr_to/sr_from), endpoint=False)
    return np.interp(t_new, t_old, x).astype(np.int16), sr_to

def apply_beep(data, sr, spans):
    out = data.copy().astype(np.int16)
    amp = int(0.6 * 32767)
    for s, e in spans:
        s_ms, e_ms = max(0, int(s*1000)-PAD_MS), int(e*1000)+PAD_MS
        s_idx, e_idx = max(0, int(s_ms*sr/1000)), min(len(out), int(e_ms*sr/1000))
        n = e_idx - s_idx
        if n <= 0: continue
        t = np.arange(n)/sr
        beep = (amp*np.sin(2*math.pi*BEEP_FREQ*t)).astype(np.int16)
        out[s_idx:e_idx] = beep
    return out

if __name__ == "__main__":
    input_file = "myvoice.wav"   # ← الملف اللي سجلتيه
    output_file = "clean.wav"    # ← الملف الناتج

    print("🔎 استخراج الكلمات...")
    words = transcribe(input_file)
    spans = find_bad_spans(words)

    if spans: print("🚨 تم العثور على شتائم:", spans)
    else: print("✅ لا توجد شتائم.")

    data, sr = load_wav(input_file)
    data, sr = resample(data, sr, SR_TARGET)

    print("🔊 تطبيق البليب...")
    out = apply_beep(data, sr, spans)
    save_wav(output_file, out, sr)
    print(f"✅ الملف الناتج: {output_file}")
