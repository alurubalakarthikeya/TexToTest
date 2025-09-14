import React, { useState, useRef } from "react";
import "./App.css";
import Navbar from "./Components/NavBar.jsx";

export default function App() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isFullyExpanded, setIsFullyExpanded] = useState(false);
  const [placeholderStyle, setPlaceholderStyle] = useState(null);
  const [inlineStyle, setInlineStyle] = useState(null);
  const [questions, setQuestions] = useState([]);
  const quizRef = useRef(null);
  const startRectRef = useRef(null);
  const DURATION = 1000; // ms

  const expandCard = () => {
    const el = quizRef.current;
    if (!el || isExpanded) return;

    const rect = el.getBoundingClientRect();
    startRectRef.current = rect;

    setPlaceholderStyle({
      width: `${rect.width}px`,
      height: `${rect.height}px`,
      display: "block",
    });

    const nav = document.querySelector(".navbar");
    const navRect = nav
      ? nav.getBoundingClientRect()
      : { bottom: 70, left: 40, width: Math.min(1200, window.innerWidth - 40) };

    const targetTop = Math.max(navRect.bottom + 12, 12);
    const targetLeft = navRect.left;
    const targetWidth = Math.min(navRect.width, window.innerWidth - 24);
    const targetHeight = Math.max(window.innerHeight - targetTop - 12, 200);

    const computedStyle = window.getComputedStyle(el);
    const startStyle = {
      position: "fixed",
      top: `${rect.top}px`,
      left: `${rect.left}px`,
      width: `${rect.width}px`,
      height: `${rect.height}px`,
      margin: 0,
      zIndex: 900,
      borderRadius: computedStyle.borderRadius || "12px",
      transition: `all ${DURATION}ms ease`,
      overflow: "auto",
    };

    setInlineStyle(startStyle);
    setIsExpanded(true);

   document.querySelector(".title").classList.add("blur-out");
   document.querySelectorAll(".card").forEach((c) => {
     if (!c.classList.contains("quiz-card")) c.classList.add("blur-out");
   });

    requestAnimationFrame(() => {
      setInlineStyle({
        ...startStyle,
        top: `${targetTop}px`,
        left: `${targetLeft}px`,
        width: `${targetWidth}px`,
        height: `${targetHeight}px`,
        borderRadius: "12px",
      });
    });

    setTimeout(() => {
      setIsFullyExpanded(true);
    }, DURATION + 1000);
  };

  const collapseCard = () => {
    if (!isExpanded) return;
    setIsFullyExpanded(false);

    const rect = startRectRef.current;
    if (!rect) {
      setIsExpanded(false);
      setInlineStyle(null);
      setPlaceholderStyle(null);
      return;
    }

    setInlineStyle((prev) => ({
      ...prev,
      transition: `all ${DURATION}ms ease`,
      width: `${rect.width}px`,
      height: `${rect.height}px`,
      top: `${rect.top}px`,
      left: `${rect.left}px`,
      borderRadius: "20px",
    }));

    setTimeout(() => {
      setIsExpanded(false);
      setInlineStyle(null);
      setPlaceholderStyle(null);
      startRectRef.current = null;

      document.querySelector(".title").classList.remove("blur-out");
      document.querySelectorAll(".card").forEach((c) => {
        if (!c.classList.contains("quiz-card")) c.classList.remove("blur-out");
      });
    }, DURATION + 100);
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    expandCard();

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://127.0.0.1:8000/upload-pdf/", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Failed to fetch quiz");
      const data = await res.json();
      setQuestions(data.questions || []);
    } catch (err) {
      console.error("Error fetching quiz:", err);
    }
  };

  const handleGenerateClick = () => {
    expandCard();
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
              <i className="fas fa-file-pdf" aria-hidden />
              <p>Upload PDF</p>
              <span>Drag and drop file here or click to select</span>
            </label>
          </div>

          <button className="btn" onClick={handleGenerateClick}>
            Generate Quiz
          </button>
        </div>

        {placeholderStyle && (
          <div className="card-placeholder" style={placeholderStyle} />
        )}

        <div
          ref={quizRef}
          className={`card quiz-card ${isExpanded ? "fixed" : ""}`}
          style={inlineStyle ? inlineStyle : undefined}
        >
          {isFullyExpanded && (
            <button
              className="quiz-close"
              onClick={collapseCard}
              aria-label="Close"
            >
              ✕
            </button>
          )}

          <h2>Generated Quiz</h2>

          {!isExpanded ? (
            <p className="quiz-instruction">
              Upload a PDF and click "Generate Quiz" to see the questions here.
            </p>
          ) : (
            <div className="question-grid" style={{ marginTop: "16px" }}>
              {questions.length > 0 ? (
                questions.map((item, idx) => (
                  <article className="question-card" key={idx}>
                    <p className="question-text">
                      Q{idx + 1}. {item.q}
                    </p>
                    <ul className="options">
                      {item.options.map((opt, i) => (
                        <li key={i} className="option">
                          <span className="opt-letter">
                            {String.fromCharCode(65 + i)}.
                          </span>
                          <span className="opt-text">{opt}</span>
                        </li>
                      ))}
                    </ul>
                  </article>
                ))
              ) : (
                <p className="quiz-instruction">
                  Processing PDF... Please wait.
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}