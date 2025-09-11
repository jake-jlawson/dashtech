import styles from "./FeedEntry.module.css";
import { useState } from "react";



export default function FeedEntry({log}: {log: any}) {
    
    const feedEntries = {
        "communications.talk": <TalkEntry log={log} />,
        "issue.created": <IssueCreatedEntry log={log} />,
    }
    
    return (
        <div className={styles.feedEntryContainer}>
            {feedEntries[log.type as keyof typeof feedEntries]}
        </div>
    )
}


function TalkEntry({log}: {log: any}) {
    const [isSpeaking, setIsSpeaking] = useState(false);
    
    const handleSpeak = () => {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(log.payload.message);
            utterance.onstart = () => setIsSpeaking(true);
            utterance.onend = () => setIsSpeaking(false);
            utterance.onerror = () => setIsSpeaking(false);
            window.speechSynthesis.speak(utterance);
        }
    };
    
    return (
        <div className={styles.messageRow}>
            <div className={styles.agentAvatar}>🤖</div>
            <div className={styles.messageBubble}>
                <div className={styles.messageText}>{log.payload.message}</div>
                <button 
                    className={styles.speakButton}
                    onClick={handleSpeak}
                    disabled={isSpeaking}
                    title={isSpeaking ? 'Speaking...' : 'Speak message'}
                >
                    {isSpeaking ? '🔊' : '🔊'}
                </button>
            </div>
        </div>
    )
}

function IssueCreatedEntry({log}: {log: any}) {
    return (
        <div className={styles.flagRow}>
            <div className={styles.flagIcon}>✓</div>
            <div className={styles.flagText}>{log.payload.message}</div>
        </div>
    )
}
