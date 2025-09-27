import joblib
from preprocess import extract_features

model = joblib.load("cough_model.pkl")

features = extract_features("sample_cough.wav")
prediction = model.predict([features])

print("predicted class:", prediction[0])
