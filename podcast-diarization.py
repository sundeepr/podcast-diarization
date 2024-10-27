from pyannote.audio import Pipeline
dia_pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token="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")

# send pipeline to GPU (when available)
import torch
dia_pipeline.to(torch.device("cuda"))

# apply pretrained pipeline
#diarization = pipeline("outputfile.mp3")


#diarization.for_json()["content"]

#print(diarization.__dir__())

# print the result
#for turn, _, speaker in diarization.itertracks(yield_label=True):
#    print(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")


from transformers import pipeline

asr_pipeline = pipeline(
    "automatic-speech-recognition",
    model="openai/whisper-base",
    device=torch.device("cuda")
)
#asr_pipeline.to(torch.device("cuda"))
#speech_reco = asr_pipeline(
#    "outputfile.mp3",
#    generate_kwargs={"max_new_tokens": 256},
#    return_timestamps=True,
#)

#print(speech_reco)

from speechbox import ASRDiarizationPipeline

asrd_pipeline = ASRDiarizationPipeline(
    asr_pipeline=asr_pipeline, diarization_pipeline=dia_pipeline
)

import torchaudio
waveform, sample_rate = torchaudio.load("practical-ai-276.mp3") 

audio_in_memory = {"raw": waveform.numpy()[0], "sampling_rate": sample_rate}
#print(f"{type(waveform)=}")
#print(f"{waveform.shape=}")
#print(f"{waveform.dtype=}")

# load dataset of concatenated LibriSpeech samples
#concatenated_librispeech = load_dataset("sanchit-gandhi/concatenated_librispeech", split="train", streaming=True)
# get first sample
#sample = next(iter(concatenated_librispeech))

out = asrd_pipeline(audio_in_memory.copy())

print(out)
