import React, { useState } from 'react';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async () => {
    if (!file) {
      setResult("Please upload a cough file.");
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('http://localhost:5000/predict', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();
    setResult(`Predicted Disease: ${data.prediction}`);
    setLoading(false);
  };

  return (
    <div className="App">
      <h1>Virufy AI Disease Detection</h1>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleSubmit}>Predict</button>
      {loading && <p>Analyzing...</p>}
      <p>{result}</p>
    </div>
  );
}

export default App;
