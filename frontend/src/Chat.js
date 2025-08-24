import React, { useState, useRef, useEffect } from "react";
import { sendMessage } from "./api";
import "./Chat.css";

function Chat() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [isSupported, setIsSupported] = useState(false);
  const [detectedLanguage, setDetectedLanguage] = useState(null);
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);
  const messagesEndRef = useRef(null);
  const isRecordingRef = useRef(false); // Add ref to track recording state
  const silenceTimerRef = useRef(null); // Add ref for silence detection timer
  const lastSpeechTimeRef = useRef(Date.now()); // Track when speech was last detected
  const [silenceTimeLeft, setSilenceTimeLeft] = useState(0); // Show silence countdown
  const [isLanguageSwitching, setIsLanguageSwitching] = useState(false); // Track language switching state
  const startSilenceDetectionRef = useRef(null); // Ref for silence detection function
  const isLanguageSwitchingRef = useRef(false); // Ref for language switching state

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Silence detection configuration
  const SILENCE_TIMEOUT = 2000; // Stop recording after 2 seconds of silence
  const SILENCE_CHECK_INTERVAL = 500; // Check for silence every 500ms

  const startSilenceDetection = () => {
    // Clear any existing timer
    if (silenceTimerRef.current) {
      clearInterval(silenceTimerRef.current);
    }

    // Start checking for silence
    silenceTimerRef.current = setInterval(() => {
      const now = Date.now();
      const timeSinceLastSpeech = now - lastSpeechTimeRef.current;
      const remainingTime = Math.max(0, SILENCE_TIMEOUT - timeSinceLastSpeech);

      setSilenceTimeLeft(remainingTime);

      if (timeSinceLastSpeech > SILENCE_TIMEOUT) {
        console.log("🔇 Silence detected, stopping recording");
        stopRecording();
        clearInterval(silenceTimerRef.current);
        silenceTimerRef.current = null;
        setSilenceTimeLeft(0);
      }
    }, SILENCE_CHECK_INTERVAL);
  };

  // Store function in ref to avoid dependency issues
  startSilenceDetectionRef.current = startSilenceDetection;

  const stopSilenceDetection = () => {
    if (silenceTimerRef.current) {
      clearInterval(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
  };

  const startRecording = () => {
    if (
      recognitionRef.current &&
      isSupported &&
      !isRecordingRef.current &&
      !isLanguageSwitchingRef.current
    ) {
      try {
        // Reset language switching state
        setIsLanguageSwitching(false);
        isLanguageSwitchingRef.current = false; // Update ref
        recognitionRef.current.start();
      } catch (error) {
        console.error("Failed to start recording:", error);
        setError("Failed to start voice recording");
      }
    } else if (isLanguageSwitchingRef.current) {
      console.log("Cannot start recording - language switch in progress");
    } else if (isRecordingRef.current) {
      console.log("Recording already in progress");
    }
  };

  const stopRecording = () => {
    if (recognitionRef.current && isRecordingRef.current) {
      recognitionRef.current.stop();
      stopSilenceDetection(); // Stop silence detection
    }
  };

  const toggleRecording = () => {
    if (isRecordingRef.current) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Check if speech recognition is supported
    if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
      setIsSupported(true);
      const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();

      // Configure speech recognition
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = "en"; // Start with English as default

      // Set up event handlers
      recognitionRef.current.onstart = () => {
        setIsRecording(true);
        isRecordingRef.current = true; // Update ref
        setTranscript("");
        setDetectedLanguage(null); // Reset language detection for new recording
        lastSpeechTimeRef.current = Date.now(); // Reset speech time on start
        startSilenceDetectionRef.current(); // Use ref instead of direct function call
      };

      recognitionRef.current.onresult = (event) => {
        let finalTranscript = "";
        let interimTranscript = "";

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }

        const currentTranscript = finalTranscript + interimTranscript;
        setTranscript(currentTranscript);
        lastSpeechTimeRef.current = Date.now(); // Update speech time on new speech

        // Auto-detect language and switch recognition language if needed
        if (currentTranscript.trim()) {
          const detectedLang = detectLanguage(currentTranscript);
          console.log("🔍 Language Detection Debug:");
          console.log("  Text:", currentTranscript);
          console.log("  Detected Language:", detectedLang);
          console.log(
            "  Current Recognition Language:",
            recognitionRef.current.lang
          );

          if (detectedLang && recognitionRef.current.lang !== detectedLang) {
            console.log(`Auto-switching to ${detectedLang} language`);

            // Prevent multiple language switches
            if (isLanguageSwitchingRef.current) {
              console.log("Language switch already in progress, skipping...");
              return;
            }

            setIsLanguageSwitching(true);
            isLanguageSwitchingRef.current = true; // Update ref

            // Store the detected language
            setDetectedLanguage(detectedLang);

            // Show language detection feedback
            if (detectedLang === "ar") {
              console.log("🎯 Detected Arabic (unified)");
            } else if (detectedLang === "en") {
              console.log("🎯 Detected English");
            }

            // Restart recognition with the new language for better accuracy
            if (isRecordingRef.current) {
              try {
                // Check if recognition is already running before stopping
                if (
                  recognitionRef.current &&
                  recognitionRef.current.state === "recording"
                ) {
                  recognitionRef.current.stop();
                  // Wait a bit longer for the stop to complete
                  setTimeout(() => {
                    try {
                      recognitionRef.current.lang = detectedLang;
                      recognitionRef.current.start();
                      setIsLanguageSwitching(false);
                      isLanguageSwitchingRef.current = false; // Update ref
                    } catch (startError) {
                      console.error(
                        "Failed to restart recognition:",
                        startError
                      );
                      // If restart fails, just update the language for next time
                      recognitionRef.current.lang = detectedLang;
                      setIsLanguageSwitching(false);
                      isLanguageSwitchingRef.current = false; // Update ref
                    }
                  }, 200); // Increased timeout for better reliability
                } else {
                  // Just update the language if not currently recording
                  recognitionRef.current.lang = detectedLang;
                  setIsLanguageSwitching(false);
                  isLanguageSwitchingRef.current = false; // Update ref
                }
              } catch (error) {
                console.error("Failed to restart recognition:", error);
                // Fallback: just update the language
                recognitionRef.current.lang = detectedLang;
                setIsLanguageSwitching(false);
                isLanguageSwitchingRef.current = false; // Update ref
              }
            } else {
              // Not recording, just update language
              recognitionRef.current.lang = detectedLang;
              setIsLanguageSwitching(false);
              isLanguageSwitchingRef.current = false; // Update ref
            }
          }
        }
      };

      recognitionRef.current.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        setIsRecording(false);
        isRecordingRef.current = false; // Update ref
        setIsLanguageSwitching(false); // Reset language switching state
        isLanguageSwitchingRef.current = false; // Update ref
        setError(`Voice recognition error: ${event.error}`);
        stopSilenceDetection(); // Stop silence detection on error
      };

      recognitionRef.current.onend = () => {
        setIsRecording(false);
        isRecordingRef.current = false; // Update ref
        setIsLanguageSwitching(false); // Reset language switching state
        isLanguageSwitchingRef.current = false; // Update ref
        // Use a callback to get the current transcript value
        setTranscript((currentTranscript) => {
          if (currentTranscript.trim()) {
            setInputValue(currentTranscript.trim());
          }
          return ""; // Clear transcript
        });
        stopSilenceDetection(); // Stop silence detection on end
      };
    }

    // Add initial assistant message
    setMessages([
      {
        id: 1,
        content:
          "Hello! I'm your AI-powered RAG chatbot assistant. I can help you find information from your uploaded documents. Simply ask me anything and I'll search through your documents to provide accurate answers.",
        role: "assistant",
        timestamp: new Date(),
      },
    ]);

    // Focus input on mount
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  useEffect(() => {
    console.log(
      "Session ID changed:",
      currentSessionId,
      typeof currentSessionId
    );
  }, [currentSessionId]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      content: inputValue,
      role: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);
    setError(null);

    try {
      const response = await sendMessage(inputValue, currentSessionId);

      // Ensure response exists and has required properties
      if (!response) {
        throw new Error("No response received from the server");
      }

      // Update session ID if this is the first message
      if (!currentSessionId && response.session_id) {
        console.log(
          "Setting new session ID:",
          response.session_id,
          typeof response.session_id
        );
        setCurrentSessionId(response.session_id);
      }

      const botMessage = {
        id: response.message_id || Date.now(),
        content:
          response.response ||
          "I'm sorry, I couldn't generate a response. Please try again.",
        role: "assistant",
        timestamp: new Date(),
        confidence: response.confidence,
        sources: response.sources || [],
        chunks_found: response.chunks_found || 0,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Chat error:", error);
      setError(error.message);

      const errorMessage = {
        id: Date.now() + 1,
        content:
          "Sorry, I encountered an error while processing your request. Please try again or check your connection.",
        role: "assistant",
        timestamp: new Date(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    console.log("Clearing chat, current session ID:", currentSessionId);
    setMessages([
      {
        id: 1,
        content:
          "Hello! I'm your AI-powered RAG chatbot assistant. I can help you find information from your uploaded documents. Simply ask me anything and I'll search through your documents to provide accurate answers.",
        role: "assistant",
        timestamp: new Date(),
      },
    ]);
    setCurrentSessionId(null);
    setError(null);
    console.log("Chat cleared, session ID reset to:", null);
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return "high";
    if (confidence >= 0.6) return "medium";
    return "low";
  };

  const getConfidenceLabel = (confidence) => {
    if (confidence >= 0.8) return "High";
    if (confidence >= 0.6) return "Medium";
    return "Low";
  };

  const formatSessionId = (sessionId) => {
    if (!sessionId) return "";
    if (typeof sessionId !== "string") return String(sessionId);
    if (sessionId.length <= 8) return sessionId;
    return `${sessionId.slice(0, 8)}...`;
  };

  // Automatic language detection function
  const detectLanguage = (text) => {
    if (!text || text.length < 3) return null;

    // Arabic character detection (Unicode range for Arabic script)
    const arabicRegex =
      /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/;

    // Essential Modern Standard Arabic words
    const msaWords = [
      "مرحبا",
      "كيف",
      "الحال",
      "شكرا",
      "من",
      "فى",
      "على",
      "الى",
      "عن",
      "مع",
      "هذا",
      "هذه",
      "ذلك",
      "تلك",
      "الذي",
      "التي",
      "الذين",
      "اللاتي",
      "اللائي",
      "ما",
      "ماذا",
      "لماذا",
      "كيف",
      "متى",
      "أين",
      "كم",
      "أي",
      "أيها",
      "أيتها",
      "هل",
      "أ",
      "أو",
      "لكن",
      "لأن",
      "إذا",
      "إن",
      "أن",
      "كان",
      "يكون",
      "كانت",
      "ال",
      "و",
      "ف",
      "ثم",
      "حيث",
      "حين",
      "بعد",
      "قبل",
      "خلال",
      "حول",
      "داخل",
    ];

    // Essential Egyptian Arabic dialect words (most common only)
    const egyptianWords = [
      // Most common Egyptian expressions
      "أهلا",
      "معلش",
      "مش مشكلة",
      "مش عايز",
      "مش عايزة",
      "إيه",
      "فين",
      "مين",
      "كام",
      "ليه",
      "عايز",
      "عايزة",
      "ممكن",
      "ماشي",
      "تمام",
      "أيوه",
      "لأ",
      "كده",
      "طيب",
      "خلاص",
    ];

    // Check for Arabic characters first
    if (arabicRegex.test(text)) {
      const textLower = text.toLowerCase();

      // Count Egyptian dialect words
      const egyptianWordCount = egyptianWords.filter((word) =>
        textLower.includes(word.toLowerCase())
      ).length;

      // Count MSA words
      const msaWordCount = msaWords.filter((word) =>
        textLower.includes(word.toLowerCase())
      ).length;

      // If any Arabic words found, return Arabic (unified)
      if (egyptianWordCount > 0 || msaWordCount > 0) {
        // Log dialect detection for debugging
        if (egyptianWordCount > msaWordCount) {
          console.log("🎯 Detected Egyptian Arabic dialect");
        } else if (msaWordCount > 0) {
          console.log("🎯 Detected Modern Standard Arabic");
        }

        // Return unified Arabic language code
        return "ar"; // Use simplified Arabic code
      }

      // Default to Arabic for any Arabic script
      return "ar";
    }

    // Check for Arabic words (case-insensitive) - fallback for non-Arabic script
    const textLower = text.toLowerCase();
    const egyptianWordCount = egyptianWords.filter((word) =>
      textLower.includes(word.toLowerCase())
    ).length;

    const msaWordCount = msaWords.filter((word) =>
      textLower.includes(word.toLowerCase())
    ).length;

    // If any Arabic words found, return Arabic (unified)
    if (egyptianWordCount > 0 || msaWordCount > 0) {
      // Log dialect detection for debugging
      if (egyptianWordCount > msaWordCount) {
        console.log("🎯 Detected Egyptian Arabic dialect");
      } else if (msaWordCount > 0) {
        console.log("🎯 Detected Modern Standard Arabic");
      }

      return "ar"; // Unified Arabic
    }

    // Default to English
    return "en-US";
  };

  return (
    <div className="chat-container">
      {/* Enhanced Header */}
      <div className="chat-header">
        <div className="chat-header-left">
          <div className="chat-title">
            <div className="chat-icon">🤖</div>
            <div>
              <h2>AI Chat Assistant</h2>
              <p className="chat-subtitle">Powered by RAG Technology</p>
            </div>
          </div>
        </div>
        <div className="chat-header-right">
          <button
            onClick={clearChat}
            className="clear-chat-btn"
            title="Clear conversation history"
          >
            <span className="btn-icon">🗑️</span>
            <span className="btn-text">Clear Chat</span>
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-banner">
          <div className="error-icon">⚠️</div>
          <div className="error-content">
            <strong>Error:</strong> {error}
          </div>
        </div>
      )}

      {/* Messages Container */}
      <div className="messages-container">
        {messages.map((message) => (
          <div key={message.id} className={`message-wrapper ${message.role}`}>
            <div
              className={`message ${message.role} ${
                message.isError ? "error" : ""
              }`}
            >
              {/* Message Avatar */}
              <div className="message-avatar">
                {message.role === "user" ? "👤" : "🤖"}
              </div>

              {/* Message Content */}
              <div className="message-content">
                <div className="message-text">{message.content}</div>

                {/* Sources Section */}
                {message.sources && message.sources.length > 0 && (
                  <div className="message-sources">
                    <div className="sources-header">
                      <span className="sources-icon">📄</span>
                      <strong>Sources Found:</strong>
                    </div>
                    <div className="sources-list">
                      {message.sources.map((source, idx) => (
                        <div key={idx} className="source-item">
                          <div className="source-filename">
                            {source.filename}
                            {source.page_number && (
                              <span className="source-page">
                                {" "}
                                (Page {source.page_number})
                              </span>
                            )}
                          </div>
                          {source.similarity_score && (
                            <div className="source-match">
                              {Math.round(source.similarity_score * 100)}% match
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Message Footer */}
                <div className="message-footer">
                  <span className="message-time">
                    {formatTime(message.timestamp)}
                  </span>

                  {message.confidence !== undefined && (
                    <div
                      className={`confidence-badge confidence-${getConfidenceColor(
                        message.confidence
                      )}`}
                    >
                      {getConfidenceLabel(message.confidence)} Confidence
                    </div>
                  )}

                  {message.chunks_found > 0 && (
                    <div className="chunks-info">
                      📊 {message.chunks_found} relevant chunks found
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="message-wrapper assistant">
            <div className="message assistant loading">
              <div className="message-avatar">🤖</div>
              <div className="message-content">
                <div className="typing-indicator">
                  <div className="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <span className="typing-text">AI is thinking...</span>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Enhanced Input Form */}
      <form onSubmit={handleSend} className="chat-input-form">
        <div className="input-container">
          {/* Voice Input Button */}
          {isSupported && (
            <div className="voice-controls">
              {/* Language Selection */}
              <select
                className="language-selector"
                value={recognitionRef.current?.lang || "en"}
                onChange={(e) => {
                  if (recognitionRef.current) {
                    recognitionRef.current.lang = e.target.value;
                    setDetectedLanguage(e.target.value);
                  }
                }}
                disabled={isRecording}
              >
                <option value="en">EN - English</option>
                <option value="ar">AR - Arabic (Egyptian & Modern)</option>
              </select>

              <button
                type="button"
                onClick={toggleRecording}
                className={`voice-button ${isRecording ? "recording" : ""}`}
                title={isRecording ? "Stop recording" : "Start voice input"}
                disabled={isLoading}
              >
                {isRecording ? (
                  <span className="voice-icon recording">🎤</span>
                ) : (
                  <span className="voice-icon">🎤</span>
                )}
              </button>

              {/* Silence Indicator */}
              {isRecording && silenceTimeLeft > 0 && (
                <div className="silence-indicator">
                  <span className="silence-icon">🔇</span>
                  <span className="silence-text">
                    Auto-stop in {Math.ceil(silenceTimeLeft / 1000)}s
                  </span>
                </div>
              )}

              {/* Language Switching Indicator */}
              {isLanguageSwitching && (
                <div className="language-switching-indicator">
                  <span className="switching-icon">🔄</span>
                  <span className="switching-text">Switching language...</span>
                </div>
              )}
            </div>
          )}

          {/* Browser Compatibility Message */}
          {!isSupported && (
            <div className="voice-compatibility-message">
              <span className="compatibility-icon">ℹ️</span>
              <span className="compatibility-text">
                Voice input not supported in this browser
              </span>
            </div>
          )}

          {/* Voice Transcript Display */}
          {transcript && (
            <div className="voice-transcript">
              <span className="transcript-label">🎤</span>
              <span className="transcript-text">{transcript}</span>
              {detectedLanguage && (
                <span className="language-indicator">
                  {detectedLanguage === "ar" && "🇸🇦 Arabic"}
                  {detectedLanguage === "en" && "🇺🇸 English"}
                </span>
              )}
            </div>
          )}

          <input
            ref={inputRef}
            type="text"
            className="chat-input"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask me anything about your uploaded documents..."
            disabled={isLoading}
            maxLength={500}
          />
          <div className="input-actions">
            <div className="char-count">{inputValue.length}/500</div>
            <button
              type="submit"
              className="send-button"
              disabled={!inputValue.trim() || isLoading}
              title={
                !inputValue.trim() ? "Please enter a message" : "Send message"
              }
            >
              {isLoading ? (
                <span className="send-loading">
                  <div className="send-spinner"></div>
                </span>
              ) : (
                <>
                  <span className="send-icon">📤</span>
                  <span className="send-text">Send</span>
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Session Info */}
      {currentSessionId && (
        <div className="session-info">
          <div className="session-badge">
            <span className="session-icon">🔗</span>
            Session: {formatSessionId(currentSessionId)}
          </div>
        </div>
      )}

      {/* Quick Tips */}
      <div className="quick-tips">
        <div className="tips-header">
          <span className="tips-icon">💡</span>
          <span>Quick Tips</span>
        </div>
        <div className="tips-content">
          <div className="tip">
            <strong>Voice Input:</strong> Click the microphone button to ask
            questions using your voice
          </div>
          <div className="tip">
            <strong>Auto Language Detection:</strong> I automatically detect
            English or Arabic (Egyptian & Modern Standard)
          </div>
          <div className="tip">
            <strong>Arabic Support:</strong> Speak naturally in Egyptian Arabic
            or Modern Standard Arabic
          </div>
          <div className="tip">
            <strong>Silence Detection:</strong> Recording automatically stops
            after 2 seconds of silence
          </div>
          <div className="tip">
            <strong>Clear Questions:</strong> Ask specific questions for better
            document search results
          </div>
          <div className="tip">
            <strong>Document References:</strong> I'll show you which documents
            I used to answer your questions
          </div>
        </div>
      </div>
    </div>
  );
}

export default Chat;
