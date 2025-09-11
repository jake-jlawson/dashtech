import styles from "./Chat.module.css";
import { useState } from "react";
import { useIssue } from "../../hooks/useIssue";
import ChatFeed from "./ChatFeed/ChatFeed";


export default function Chat() {
    
    const { startDiagnostics, issueLog } = useIssue();
    const [chatType, setChatType] = useState<"default" | "diagnostics" | "communications">("default");

    

    const handleStartDiagnostics = () => {
        setChatType("diagnostics");
        startDiagnostics();
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
                    <button className={styles.voiceDemoButton}>🔊 Test Voice Output</button>
                </div>
            </div>

            {/* Right Column - Results */}
            <div className={`${styles.column} ${styles.columnRight}`}>
                
                <h3 className={styles.sectionTitle}>Diagnostic Actions</h3>
                
                <div className={styles.actionsSection}>
                    <div className={`${styles.actionsFeed}`}>
                        
                        {
                            chatType === "diagnostics" ? (
                                <ChatFeed issueLog={issueLog} />
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
                                    type="text"
                                    placeholder="Enter diagnostic question..."
                                    className={styles.textInput}
                                />
                                <button className={styles.iconButton} title="Start voice input">🎤</button>
                            </div>
                            
                        </div>
                    </div>
                </div>
                
            </div>
        </div>
    )
}