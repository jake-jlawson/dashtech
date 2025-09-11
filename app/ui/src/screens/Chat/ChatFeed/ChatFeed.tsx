

import styles from "./ChatFeed.module.css";
import FeedEntry from "../FeedEntries/FeedEntry";
import { useEffect, useRef } from "react";


interface ChatFeedProps {
    issueLog: any[];
    onSubmitTestResult?: (testId: string, result: any) => void;
    loading?: boolean;
    thinking?: string;
}

export default function ChatFeed({issueLog, onSubmitTestResult, loading, thinking}: ChatFeedProps) {
    const thinkingScrollRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        if (thinkingScrollRef.current) {
            thinkingScrollRef.current.scrollTop = thinkingScrollRef.current.scrollHeight;
        }
    }, [thinking]);
    return (
        <div className={styles.chatFeed}>
            <div className={`${styles.chats}`}>
                {issueLog && issueLog.map((log, index) => (
                    <FeedEntry key={index} log={log} onSubmitTestResult={onSubmitTestResult} />
                ))}
                {loading && (
                    <div className={styles.loadingRow}>
                        <div className={styles.loader} aria-label="Loading" />
                        <div className={styles.loadingText}>Thinking…</div>
                    </div>
                )}
                {thinking && thinking.length > 0 && (
                    <div className={styles.thinkingRow}>
                        <div className={styles.thinkingScroll} ref={thinkingScrollRef}>
                            <div className={styles.thinkingText}>{thinking}</div>
                        </div>
                    </div>
                )}
            </div>
            
        </div>
    )
}