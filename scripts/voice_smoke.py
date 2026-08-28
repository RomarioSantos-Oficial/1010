import json
from time import perf_counter

from config.settings import ROOT, settings
from speech.faster_whisper_provider import FasterWhisperProvider
from speech.kokoro_provider import KokoroProvider
from speech.piper_provider import PiperProvider


def main() -> None:
    output = ROOT / "outputs" / "voice" / "smoke_pt_br.wav"
    output.parent.mkdir(parents=True, exist_ok=True)
    phrase = "Olá, eu sou Luna. A voz e o reconhecimento local estão funcionando."

    if settings.tts_provider == "kokoro":
        tts = KokoroProvider(
            settings.tts_kokoro_model_dir,
            voice=settings.tts_voice,
            language=settings.tts_language,
            device=settings.tts_device,
            speed=settings.tts_speed,
            enabled=settings.tts_enabled,
        )
    else:
        tts = PiperProvider(settings.tts_model_path, settings.tts_use_cuda, settings.tts_length_scale)
    started = perf_counter()
    audio = tts.synthesize(phrase)
    tts_latency = perf_counter() - started
    output.write_bytes(audio.data)

    stt = FasterWhisperProvider(settings.stt_model_path, settings.stt_device, settings.stt_compute_type)
    started = perf_counter()
    transcription = stt.transcribe(audio.data, "pt")
    stt_latency = perf_counter() - started
    if not transcription.text:
        raise RuntimeError("O modelo real de STT não detectou a frase sintetizada.")

    print(json.dumps({
        "wav": str(output),
        "bytes": len(audio.data),
        "audio_duration_seconds": round(audio.duration, 3),
        "tts_latency_seconds": round(tts_latency, 3),
        "stt_latency_seconds": round(stt_latency, 3),
        "transcript": transcription.text,
        "detected_language": transcription.language,
        "tts_provider": tts.name,
        "tts_voice": getattr(tts, "voice", "configured"),
        "tts_voice_gender": getattr(tts, "voice_gender", "unknown"),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
