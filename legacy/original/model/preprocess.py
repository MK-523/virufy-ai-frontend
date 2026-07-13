
import numpy as np
import librosa

def extract_features(audio_path):
    y, sr = librosa.load(audio_path, sr=22050)
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    return np.mean(mfccs.T, axis=0)

if __name__ == "__main__":
    features = extract_features("sample_cough.wav")
    print("extracted features:", features)
