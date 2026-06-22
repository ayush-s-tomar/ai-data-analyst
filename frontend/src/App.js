import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import axios from 'axios';
import './App.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [step, setStep] = useState('upload');
  const [fileData, setFileData] = useState(null);
  const [csvData, setCsvData] = useState('');
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const chatEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleFileUpload = async (file) => {
    if (!file || !file.name.endsWith('.csv')) {
      setError('Please upload a CSV file');
      return;
    }
    setError('');
    setStep('analyzing');
    setLoading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE}/analyze`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      const data = response.data;
      setFileData(data);
      setCsvData(data.csv_data);
      setMessages([{
        role: 'assistant',
        content: data.initial_analysis,
        isInitial: true,
        timestamp: new Date()
      }]);
      setStep('chat');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze file');
      setStep('upload');
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileUpload(file);
  };

  const handleQuestion = async (e) => {
    e.preventDefault();
    if (!question.trim() || loading) return;

    const userMessage = { role: 'user', content: question, timestamp: new Date() };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setQuestion('');
    setLoading(true);
    setError('');

    // Full conversation history sent to backend (excluding initial analysis)
    const historyForAPI = messages
      .filter(m => !m.isInitial && m.role && m.content)
      .map(m => ({ role: m.role, content: m.content }));

    try {
      const response = await axios.post(`${API_BASE}/query`, {
        question: question,
        csv_data: csvData,
        history: historyForAPI
      });

      const data = response.data;
      setMessages([...newMessages, {
        role: 'assistant',
        content: data.ai_response,
        codeOutput: data.code_output,
        charts: data.charts,
        codeError: data.code_error,
        timestamp: new Date()
      }]);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to process question');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setStep('upload');
    setFileData(null);
    setMessages([]);
    setCsvData('');
    setError('');
  };

  const conversationCount = messages.filter(m => !m.isInitial).length;
  const formatTime = (date) => date?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  const suggestedQuestions = [
    "Show me a bar chart of sales by region",
    "What's the trend in profit over time?",
    "Which product performs best?",
    "Compare sales across customer segments",
    "Show me the top 5 performing days"
  ];

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <span className="logo-icon">📊</span>
            <span className="logo-text">AI Data Analyst</span>
          </div>

          {fileData && (
            <div className="file-badge">
              <span>📄</span>
              <span>{fileData.filename}</span>
              <span className="badge-stats">{fileData.rows.toLocaleString()} rows · {fileData.columns} cols</span>
            </div>
          )}

          {step === 'chat' && conversationCount > 0 && (
            <div className="memory-pill">
              <span className="memory-dot"></span>
              🧠 {conversationCount} message{conversationCount !== 1 ? 's' : ''} in memory
            </div>
          )}

          {step === 'chat' && (
            <button className="btn-secondary" onClick={handleReset}>
              + New File
            </button>
          )}
        </div>
      </header>

      <main className="main">
        {/* Upload Step */}
        {(step === 'upload' || step === 'analyzing') && (
          <div className="upload-container">
            <div className="upload-hero">
              <h1>Analyze your data with AI</h1>
              <p>Upload any CSV file and ask questions in plain English. Get instant insights, charts, and analysis — with full conversation memory.</p>
            </div>

            {step === 'analyzing' ? (
              <div className="analyzing-card">
                <div className="spinner"></div>
                <h3>Analyzing your data...</h3>
                <p>AI is examining your dataset and preparing insights</p>
              </div>
            ) : (
              <div
                className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
                onDrop={handleDrop}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  style={{ display: 'none' }}
                  onChange={(e) => e.target.files[0] && handleFileUpload(e.target.files[0])}
                />
                <div className="upload-icon">📂</div>
                <h3>Drop your CSV file here</h3>
                <p>or click to browse</p>
                <span className="upload-hint">Supports any CSV file</span>
              </div>
            )}

            {error && <div className="error-box">⚠️ {error}</div>}

            <div className="features">
              <div className="feature"><span>🤖</span><span>AI-powered analysis</span></div>
              <div className="feature"><span>📈</span><span>Auto-generated charts</span></div>
              <div className="feature"><span>🧠</span><span>Conversation memory</span></div>
              <div className="feature"><span>🐍</span><span>Python code execution</span></div>
            </div>
          </div>
        )}

        {/* Chat Step */}
        {step === 'chat' && (
          <div className="chat-container">
            {/* Sidebar */}
            {fileData && (
              <div className="sidebar">
                <div className="sidebar-section">
                  <h3>Dataset Columns</h3>
                  <div className="columns-list">
                    {fileData.columns_info.map(col => (
                      <div key={col.name} className="column-item">
                        <div className="column-name">{col.name}</div>
                        <div className="column-meta">
                          <span className="dtype-badge">{col.dtype}</span>
                          <span className="col-stat">{col.unique} unique</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Memory panel */}
                <div className="sidebar-section memory-panel">
                  <h3>Session Memory</h3>
                  {conversationCount === 0 ? (
                    <p className="memory-empty">Ask your first question to start building memory</p>
                  ) : (
                    <div className="memory-list">
                      {messages.filter(m => m.role === 'user').map((m, i) => (
                        <div key={i} className="memory-item">
                          <span className="memory-index">{i + 1}</span>
                          <span className="memory-q">{m.content.length > 45 ? m.content.slice(0, 45) + '...' : m.content}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            <div className="chat-area">
              {/* Messages */}
              <div className="messages">
                {messages.map((msg, i) => (
                  <div key={i} className={`message message-${msg.role}`}>
                    <div className="message-avatar">
                      {msg.role === 'assistant' ? '🤖' : '👤'}
                    </div>
                    <div className="message-content">
                      <div className="message-meta">
                        {msg.isInitial && <span className="initial-badge">📊 Initial Analysis</span>}
                        <span className="message-time">{formatTime(msg.timestamp)}</span>
                      </div>

                      <div className="message-text">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>

                      {msg.codeOutput && (
                        <div className="code-output">
                          <div className="code-output-header"><span>⚡ Output</span></div>
                          <pre>{msg.codeOutput}</pre>
                        </div>
                      )}

                      {msg.codeError && (
                        <div className="code-error">
                          <div className="code-error-header">⚠️ Code Error</div>
                          <pre>{msg.codeError}</pre>
                        </div>
                      )}

                      {msg.charts && msg.charts.length > 0 && (
                        <div className="charts-grid">
                          {msg.charts.map((chart, ci) => (
                            <div key={ci} className="chart-wrapper">
                              <img src={chart} alt={`Chart ${ci + 1}`} />
                              <a href={chart} download={`chart-${ci + 1}.png`} className="chart-download">
                                ⬇ Download
                              </a>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}

                {loading && (
                  <div className="message message-assistant">
                    <div className="message-avatar">🤖</div>
                    <div className="message-content">
                      <div className="typing-indicator">
                        <span></span><span></span><span></span>
                      </div>
                      <span className="typing-label">Analyzing with memory context...</span>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              {/* Suggested questions */}
              {messages.length <= 1 && (
                <div className="suggestions">
                  <p>Try asking:</p>
                  <div className="suggestion-chips">
                    {suggestedQuestions.map((q, i) => (
                      <button key={i} className="chip" onClick={() => setQuestion(q)}>
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Memory context bar */}
              {conversationCount > 0 && (
                <div className="memory-bar">
                  <span className="memory-dot"></span>
                  🧠 AI remembers your last {conversationCount} message{conversationCount !== 1 ? 's' : ''} — ask follow-up questions naturally
                  {conversationCount >= 8 && <span className="memory-warn"> · Memory near limit, consider starting a new session</span>}
                </div>
              )}

              {/* Input */}
              <form className="chat-input" onSubmit={handleQuestion}>
                <input
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder={conversationCount > 0 ? "Ask a follow-up or a new question..." : "Ask a question about your data..."}
                  disabled={loading}
                />
                <button type="submit" disabled={loading || !question.trim()}>
                  {loading ? '...' : 'Send →'}
                </button>
              </form>

              {error && <div className="error-box">⚠️ {error}</div>}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
