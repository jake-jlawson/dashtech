import styles from "./Chat.module.css";
import { useState, useRef } from "react";
import { useIssue } from "../../hooks/useIssue";
import { invoke } from "@tauri-apps/api/core";
import ChatFeed from "./ChatFeed/ChatFeed";


export default function Chat() {
    
    const { startDiagnostics, issueLog, sendIssueBegin, submitTestResult, loading, thinking } = useIssue();
    const [chatType, setChatType] = useState<"default" | "diagnostics" | "communications">("default");
    const [isListening, setIsListening] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [userInput, setUserInput] = useState("");
    const inputRef = useRef<HTMLInputElement>(null);

    const handleStartDiagnostics = () => {
        setChatType("diagnostics");
        startDiagnostics();
    }

    const handleVoiceInput = async () => {
        if (isListening) return;
        
        setIsListening(true);
        try {
            // Use the longer recording duration for better results
            const transcription = await invoke("start_voice_input_long") as string;
            setUserInput(transcription);
            if (inputRef.current) {
                inputRef.current.value = transcription;
            }
        } catch (error) {
            console.error("Voice input failed:", error);
            alert(`Voice input failed: ${error}`);
        } finally {
            setIsListening(false);
        }
    }

    const handleSpeak = (text: string) => {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.onstart = () => setIsSpeaking(true);
            utterance.onend = () => setIsSpeaking(false);
            utterance.onerror = () => setIsSpeaking(false);
            window.speechSynthesis.speak(utterance);
        }
    }

    const handleSubmit = () => {
        if (userInput.trim()) {
            if (chatType !== "diagnostics") setChatType("diagnostics");
            sendIssueBegin(userInput);
            setUserInput("");
            if (inputRef.current) {
                inputRef.current.value = "";
            }
        }
    }
    
    
    
    
    
    
    return (
        <div className={`${styles.chat}`}>
            {/* Left Column - Actions & Input */}
            <div className={`${styles.column} ${styles.columnLeft}`}>
                <h3 className={styles.sectionTitle}>Diagnostic Results</h3>
                    <div className={styles.resultsSection}>
                        <div className={styles.resultsText}>
                            Diagnostic results will appear here<br />
                            once you submit a query
                        </div>
                    <button 
                        className={styles.voiceDemoButton}
                        onClick={() => handleSpeak("Hello! This is Dashtech voice assistant. I'm ready to help with your vehicle diagnostics.")}
                        disabled={isSpeaking}
                    >
                        {isSpeaking ? '🔊 Speaking...' : '🔊 Test Voice Output'}
                    </button>
                </div>
            </div>

            {/* Right Column - Results */}
            <div className={`${styles.column} ${styles.columnRight}`}>
                
                <h3 className={styles.sectionTitle}>Diagnostic Actions</h3>
                
                <div className={styles.actionsSection}>
                    <div className={`${styles.actionsFeed}`}>
                        
                        {
                            chatType === "diagnostics" ? (
                                <ChatFeed issueLog={issueLog} onSubmitTestResult={submitTestResult} loading={loading} thinking={thinking} />
                            )
                            : (
                                <div className={`${styles.actionsGridContainer}`}>
                                    <div className={styles.actionsGrid}>
                                        {[{ icon: "⚙", label: "Run Diagnostics" }, { icon: "#", label: "Search Error Code" }, { icon: "💡", label: "Troubleshoot" }, { icon: "💬", label: "Ask Question" }].map((action, index) => (
                                            <div className={styles.actionCard} key={index} onClick={handleStartDiagnostics}>
                                                <div className={styles.actionIcon}>{action.icon}</div>
                                                <span className={styles.actionLabel}>{action.label}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )
                        }
                    </div>
                    
                    <div className={styles.inputContainer}>
                        <div className={styles.inputSection}>
                            <div className={styles.inputRow}>
                                <input
                                    ref={inputRef}
                                    type="text"
                                    placeholder="Describe your problem and press Enter..."
                                    className={styles.textInput}
                                    value={userInput}
                                    onChange={(e) => setUserInput(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
                                />
                                <button 
                                    className={styles.iconButton} 
                                    title={isListening ? 'Recording...' : 'Start voice input'}
                                    onClick={handleVoiceInput}
                                    disabled={isListening}
                                >
                                    {isListening ? '🎤...' : '🎤'}
                                </button>
                                <button 
                                    className={styles.iconButton} 
                                    title="Submit question"
                                    onClick={handleSubmit}
                                >
                                    ➤
                                </button>
                            </div>
                            
                        </div>
                    </div>
                </div>
                
            </div>
        </div>
    )
}