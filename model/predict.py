import joblib
from preprocess import extract_features

model = joblib.load('cough_model.pkl')

def predict_cough(audio_path):
    features = extract_features(audio_path)
    prediction = model.predict([features])[0]
    diseases = {0: "Healthy", 1: "Ill"}
    return diseases.get(prediction, "Unknown")
