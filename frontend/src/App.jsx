import React, { useState, useRef } from "react";
import "./App.css";
import Navbar from "./Components/NavBar.jsx";

// API base dynamic: Vite env or window override or fallback to local
const API_BASE = (
  import.meta?.env?.VITE_API_BASE ||
  (typeof window !== 'undefined' && window.__API_BASE__) ||
  "http://localhost:8000"
).replace(/\/$/, "");

export default function App() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isFullyExpanded, setIsFullyExpanded] = useState(false);
  const [placeholderStyle, setPlaceholderStyle] = useState(null);
  const [inlineStyle, setInlineStyle] = useState(null);

  const [questions, setQuestions] = useState([]);
  const [response, setResponse] = useState(""); // model output state
  const [uploadedFiles, setUploadedFiles] = useState([]); // ✅ store multiple uploaded files
  const [isLoading, setIsLoading] = useState(false);
  const [canGenerate, setCanGenerate] = useState(false); // becomes true after successful upload
  const [questionType, setQuestionType] = useState("multiple_choice");
  const [difficulty, setDifficulty] = useState("");
  const [numQuestions, setNumQuestions] = useState(25);
  const [availableFormats, setAvailableFormats] = useState({});
  const [showExportMenu, setShowExportMenu] = useState(false);

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
    
    // For mobile devices, center horizontally
    const isMobile = window.innerWidth <= 768;
    const targetWidth = isMobile 
      ? Math.min(window.innerWidth - 24, 400) 
      : Math.min(navRect.width, window.innerWidth - 24);
    const targetLeft = isMobile 
      ? (window.innerWidth - targetWidth) / 2 
      : navRect.left;
    
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

  const handleGenerateClick = async () => {
    expandCard();
    setIsLoading(true);
    setResponse(`Generating ${questionType.replace('_', ' ')} questions...`);

    try {
      const requestBody = { 
        num_questions: numQuestions, 
        question_type: questionType 
      };
      
      if (difficulty) {
        requestBody.difficulty = difficulty;
      }

      const res = await fetch(`${API_BASE}/ask-model`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      if (!res.ok) {
        let serverMsg = "";
        try {
          const data = await res.json();
          serverMsg = typeof data === 'string' ? data : (data.detail || JSON.stringify(data));
        } catch (_) {
          serverMsg = await res.text();
        }
        throw new Error(serverMsg || `Request failed with ${res.status}`);
      }

      const data = await res.json();
      setQuestions(data.questions || []);
      setResponse(`Generated ${data.questions?.length || 0} ${questionType.replace('_', ' ')} questions successfully!`);
    } catch (err) {
      console.error("Error fetching questions:", err);
      const msg = String(err?.message || err);
      // Show backend detail when available
      setResponse(msg.includes("No context")
        ? "No context on server. Please upload a file again and retry."
        : `Error while generating: ${msg}`);
    } finally {
      setIsLoading(false);
    }
  };

  // 🔹 Upload files (just collect them, don't expand yet)
  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    setUploadedFiles((prev) => [...prev, ...files.map((f) => f.name)]);

    const formData = new FormData();
    formData.append("file", files[files.length - 1]);

    try {
      const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: formData });
      if (!res.ok) {
        let serverMsg = "";
        try {
          const data = await res.json();
          serverMsg = typeof data === 'string' ? data : (data.detail || JSON.stringify(data));
        } catch (_) {
          serverMsg = await res.text();
        }
        throw new Error(serverMsg || `Upload failed with ${res.status}`);
      }
      const data = await res.json();
      setResponse(`File uploaded: ${data.filename}. Click "Generate Quiz" to create questions.`);
      setQuestions([]);
      setCanGenerate(true);
    } catch (err) {
      console.error("Error uploading file:", err);
      setResponse(`Upload error: ${err?.message || err}`);
      setCanGenerate(false);
    }
  };

  const fetchExportFormats = async () => {
    try {
      const res = await fetch(`${API_BASE}/export-formats`);
      const data = await res.json();
      setAvailableFormats(data.format_details || {});
    } catch (err) {
      console.error("Failed to fetch export formats:", err);
    }
  };

  const handleExport = async (format) => {
    if (questions.length === 0) {
      alert("No questions to export. Generate questions first.");
      return;
    }

    try {
      const exportData = {
        questions: questions,
        format_type: format,
        title: "TexToTest Generated Quiz",
        metadata: {
          question_type: questionType,
          difficulty: difficulty || "mixed",
          generated_by: "TexToTest"
        }
      };

      const res = await fetch(`${API_BASE}/export`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(exportData),
      });

      if (!res.ok) {
        throw new Error(`Export failed: ${res.statusText}`);
      }

      // Handle binary downloads (PDF, DOCX)
      if (format === 'pdf' || format === 'docx') {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `quiz.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      } else {
        // Handle text downloads (JSON, TXT, XML)
        const data = await res.json();
        const blob = new Blob([data.content], { type: data.content_type });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = data.filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      }

      setShowExportMenu(false);
    } catch (err) {
      console.error("Export error:", err);
      alert(`Export failed: ${err.message}`);
    }
  };

  // Fetch export formats on component mount
  React.useEffect(() => {
    fetchExportFormats();
  }, []);

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
              id="fileUpload"
              accept="application/pdf,.txt,.md"
              onChange={handleFileUpload}
              multiple 
              style={{ display: "none" }}
            />
            <label htmlFor="fileUpload" className="upload-label">
              <i className="fas fa-file-upload" aria-hidden />
              <p>Upload Documents</p>
              <span>PDF, TXT, MD files supported</span>
            </label>
          </div>

          {/* Question Configuration */}
          <div className="question-config">
            <div className="config-row">
              <div className="config-item">
                <label htmlFor="questionType">Question Type:</label>
                <select 
                  id="questionType" 
                  value={questionType} 
                  onChange={(e) => setQuestionType(e.target.value)}
                  className="config-select"
                >
                  <option value="multiple_choice">Multiple Choice</option>
                </select>
              </div>

              <div className="config-item">
                <label htmlFor="difficulty">Difficulty:</label>
                <select 
                  id="difficulty" 
                  value={difficulty} 
                  onChange={(e) => setDifficulty(e.target.value)}
                  className="config-select"
                >
                  <option value="">Any</option>
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>
              </div>

              <div className="config-item">
                <label htmlFor="numQuestions">Questions:</label>
                <input 
                  type="number" 
                  id="numQuestions"
                  min="5" 
                  max="50" 
                  value={numQuestions} 
                  onChange={(e) => setNumQuestions(parseInt(e.target.value) || 25)}
                  className="config-input"
                />
              </div>
            </div>
          </div>

          <button className="btn" onClick={handleGenerateClick} disabled={!canGenerate || isLoading}>
            {isLoading ? "Generating..." : (!canGenerate ? "Upload a file first" : "Generate Quiz")}
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
            <div className="quiz-header">
              <button
                className="quiz-close"
                onClick={collapseCard}
                aria-label="Close"
              >
                ✕
              </button>
              
              {questions.length > 0 && (
                <div className="quiz-actions">
                  <button
                    className="export-btn"
                    onClick={() => setShowExportMenu(!showExportMenu)}
                  >
                    📥 Export Quiz
                  </button>
                  
                  {showExportMenu && (
                    <div className="export-menu">
                      {Object.entries(availableFormats).map(([format, info]) => (
                        <button
                          key={format}
                          className={`export-option ${info.available ? '' : 'disabled'}`}
                          onClick={() => info.available && handleExport(format)}
                          disabled={!info.available}
                          title={info.description}
                        >
                          {info.label} {!info.available && '(unavailable)'}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          <h2>Generated Quiz</h2>

          {/* Show model response */}
          {response && (
            <div className="output-box">
              <h3>Model Response:</h3>
              <p>{response}</p>
              {uploadedFiles.length > 0 && (
              <div className="uploaded-files">
                <h4>Uploaded Files:</h4>
                <ul>
                  {uploadedFiles.map((fileName, idx) => (
                    <li key={idx} className="file-item">
                      <i className="fas fa-check-circle"></i>
                      {fileName}
                    </li>
                  ))}
                </ul>
              </div>
            )}
              <br />
            </div>
          )}

          {isFullyExpanded && (
            <div className="mcq-container">
              {isLoading ? (
                <div className="loading-container">
                  <div className="loading-spinner"></div>
                  <h3>Generating Questions...</h3>
                  <p>Using OpenRouter Mistral AI to create multiple-choice questions with distractors</p>
                </div>
              ) : questions.length > 0 ? (
                questions.map((question, idx) => (
                  <div className="question-card" key={idx} style={{animationDelay: `${idx * 0.1}s`}}>
                    <div className="question-header">
                      <span className="question-number">Q{idx + 1}</span>
                      <div className="question-meta">
                        <span className="question-type">{question.type?.replace('_', ' ') || 'Multiple Choice'}</span>
                        {question.difficulty && (
                          <span className={`difficulty ${question.difficulty}`}>
                            {question.difficulty.toUpperCase()}
                          </span>
                        )}
                      </div>
                      <h3 className="question-text">{question.question}</h3>
                    </div>
                    
                    <div className="question-content">
                      {/* Multiple Choice Questions */}
                      {question.type === 'multiple_choice' && question.options && (
                        <div className="options-container">
                          {Object.entries(question.options).map(([letter, text]) => (
                            <label className="option-label" key={letter}>
                              <input 
                                type="radio" 
                                name={`question-${idx}`} 
                                value={letter}
                                className="option-input"
                              />
                              <div className="option-content">
                                <span className="option-letter">{letter}.</span>
                                <span className="option-text">{text}</span>
                              </div>
                            </label>
                          ))}
                        </div>
                      )}

                      {/* True/False Questions */}
                      {question.type === 'true_false' && (
                        <div className="tf-container">
                          <label className="option-label">
                            <input type="radio" name={`question-${idx}`} value="true" />
                            <div className="option-content">
                              <span className="option-letter">True</span>
                            </div>
                          </label>
                          <label className="option-label">
                            <input type="radio" name={`question-${idx}`} value="false" />
                            <div className="option-content">
                              <span className="option-letter">False</span>
                            </div>
                          </label>
                        </div>
                      )}

                      {/* Fill in the Blank */}
                      {question.type === 'fill_in_blank' && (
                        <div className="fib-container">
                          <input 
                            type="text" 
                            className="fill-input" 
                            placeholder="Enter your answer..."
                          />
                        </div>
                      )}

                      {/* Short Answer */}
                      {question.type === 'short_answer' && (
                        <div className="sa-container">
                          <textarea 
                            className="short-answer-input" 
                            placeholder="Write your answer here..."
                            rows="3"
                          />
                        </div>
                      )}

                      {/* Matching */}
                      {question.type === 'matching' && question.left_items && question.right_items && (
                        <div className="matching-container">
                          <div className="matching-columns">
                            <div className="left-column">
                              <h4>Match these:</h4>
                              {question.left_items.map((item, i) => (
                                <div key={i} className="match-item left-item">
                                  {i + 1}. {item}
                                </div>
                              ))}
                            </div>
                            <div className="right-column">
                              <h4>With these:</h4>
                              {question.right_items.map((item, i) => (
                                <div key={i} className="match-item right-item">
                                  {String.fromCharCode(65 + i)}. {item}
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                    
                    <div className="question-footer">
                      <div className="question-info">
                        {question.category && (
                          <span className="category">📚 {question.category}</span>
                        )}
                        <span className="points">⭐ {question.points || 1} pt(s)</span>
                      </div>
                      
                      <button
                       className="reveal-answer-btn"
                       onClick={(e) => {
                         const btn = e.currentTarget;
                         const footer = btn.closest('.question-footer');
                         if (!footer) return;
                         const explanation = footer.querySelector('.explanation');
                         if (!explanation) return;
                         if (explanation.style.display === 'none' || !explanation.style.display) {
                           explanation.style.display = 'block';
                           btn.textContent = 'Hide Answer';
                         } else {
                           explanation.style.display = 'none';
                           btn.textContent = 'Show Answer';
                         }
                       }}
                     >
                       Show Answer
                     </button>
                     
                      <div className="explanation" style={{display: 'none'}}>
                        <strong>Correct Answer: {question.correct_answer}</strong>
                        <p>{question.explanation}</p>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="empty-state">
                  <h3>No Questions Generated Yet</h3>
                  <p>Upload a PDF file and click "Generate Quiz" to see multiple-choice questions here.</p>
                </div>
              )}
            </div>
          )}
          
          {!isFullyExpanded && (
            <div className="quiz-preview">
              <p className="quiz-instruction">
                {questions.length > 0 
                  ? `${questions.length} questions ready! Click to expand and view.`
                  : "Upload a PDF and click 'Generate Quiz' to see questions here."
                }
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
