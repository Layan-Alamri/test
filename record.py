import sounddevice as sd, wave

SR = 16000
DURATION = 10  # مدة التسجيل بالثواني

print(f"🎙️ Recording {DURATION} seconds... تكلم/ي الآن")
audio = sd.rec(int(DURATION*SR), samplerate=SR, channels=1, dtype='int16')
sd.wait()
with wave.open("myvoice.wav", "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes(audio.tobytes())
print("✅ تم الحفظ: myvoice.wav")
