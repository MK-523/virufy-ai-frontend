function predictCough() {
    const fileInput = document.getElementById('coughInput');
    const result = document.getElementById('result');

    if (fileInput.files.length === 0) {
        result.innerText = "Please upload a cough audio file.";
        return;
    }

    //mock demo prediction
    const diseases = ["Healthy", "COVID-19", "Bronchitis", "Flu"];
    const randomPrediction = diseases[Math.floor(Math.random() * diseases.length)];

    result.innerText = `Predicted Disease: ${randomPrediction}`;
}
