# Virufy AI Disease Detection

all data is simplified and mocked to protect patient confidentiality

this repository contains a demo implementation of Virufy’s AI-driven disease detection. It includes a React frontend for user interaction and a Flask backend with a ML model on cough samples.

---

### Frontend (React)
- web interface for uploading cough samples
- predicted disease results in real-time
- loading feedback while analyzing

### Backend (Flask)
- receives audio file uploads via HTTP POST
- extracts MFCC audio features using `librosa`
- uses a Random Forest classifier to predict disease from cough audio
- fully modular structure for extension to other AI models

