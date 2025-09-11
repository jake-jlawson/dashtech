import styles from "./FeedEntry.module.css";



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
    return (
        <div className={styles.messageRow}>
            <div className={styles.agentAvatar}>🤖</div>
            <div className={styles.messageBubble}>
                <div className={styles.messageText}>{log.payload.message}</div>
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
