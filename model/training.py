import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

#mock data
X = np.random.rand(100, 13)
y = np.random.randint(0, 2, 100)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = RandomForestClassifier()
model.fit(X_train, y_train)

print("model accuracy:", model.score(X_test, y_test))

joblib.dump(model, "cough_model.pkl")
