import torch
import torch.nn.functional as F
import torchaudio
from speechbrain.inference.speaker import SpeakerRecognition


def identify_most_similar(test_path, reference_paths):
    model = SpeakerRecognition.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        savedir="pretrained_models/spkrec-ecapa-voxceleb"
    )

    # 加载 test 音频并 resample 为 16kHz
    test_waveform, test_sr = torchaudio.load(test_path)
    if test_sr != 16000:
        test_waveform = torchaudio.transforms.Resample(orig_freq=test_sr, new_freq=16000)(test_waveform)

    # 获取 test embedding
    test_embedding = model.encode_batch(test_waveform.unsqueeze(0)).squeeze(0)

    best_score = float('-inf')
    best_match = None
    all_scores = []

    for ref_path in reference_paths:
        ref_waveform, ref_sr = torchaudio.load(ref_path)
        if ref_sr != 16000:
            ref_waveform = torchaudio.transforms.Resample(orig_freq=ref_sr, new_freq=16000)(ref_waveform)

        ref_embedding = model.encode_batch(ref_waveform.unsqueeze(0)).squeeze(0)
        score = F.cosine_similarity(test_embedding, ref_embedding, dim=0).item()

        all_scores.append((ref_path, score))

        if score > best_score:
            best_score = score
            best_match = ref_path

    return best_match, best_score, all_scores
