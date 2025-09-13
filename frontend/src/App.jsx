import React, { useState } from "react";
import "./App.css";
import Navbar from "./Components/NavBar";"./Components/NavBar.jsx";

function App() {
  const [quizGenerated, setQuizGenerated] = useState(false);

  const handleFileUpload = (e) => {
    console.log(e.target.files[0]);
    setQuizGenerated(true);
  };

  return (
    <div className="app">
      <Navbar />
      <h1 className="title">
        Automatic Quiz Question Generation <br />
        from E-Learning PDFs using NLP Pipelines
      </h1>

      <div className="container">
        <div className="card">
          <div className="upload-box">
            <input
              type="file"
              id="pdfUpload"
              accept="application/pdf"
              onChange={handleFileUpload}
              style={{ display: "none" }}
            />
            <label htmlFor="pdfUpload" className="upload-label">
              <i className="fas fa-file-pdf"></i>
              <p>Upload PDF</p>
              <span>Drag and drop file here or click to select</span>
            </label>
          </div>
          <button className="btn">Generate Quiz</button>
        </div>

        <div className="card">
          <h2>Generated Quiz</h2>
          {quizGenerated ? (
            <div className="quiz-box">
              <p>What is the capital of France?</p>
              <ul>
                <li>A. Berlin</li>
                <li>B. Madrid</li>
                <li>C. London</li>
                <li>D. Paris</li>
              </ul>
            </div>
          ) : (
            <p className="placeholder">Your quiz will appear here...</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
