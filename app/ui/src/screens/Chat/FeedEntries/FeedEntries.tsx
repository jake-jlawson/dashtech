import styles from "./FeedEntries.module.css";


/**
 * ServerActionEntry
 * Feed entry used for anytime a server action is performed
 * @returns 
 */
type actionStates = "complete" | "inProgress" | "error";

interface ServerActionEntryProps {
    actionState: actionStates;
    text: string;
}

export function ServerActionEntry({actionState, text}: ServerActionEntryProps) {
    return (
        <div className={styles.feedEntryContainer}>
            {actionState === "inProgress" && (
                <div className={`${styles.statusIcon} ${styles.inProgress}`} aria-label="In progress">
                    <span className={styles.dot}></span>
                    <span className={styles.dot}></span>
                    <span className={styles.dot}></span>
                </div>
            )}
            {actionState === "complete" && (
                <div className={`${styles.statusIcon} ${styles.complete}`} aria-label="Complete">✓</div>
            )}
            {actionState === "error" && (
                <div className={`${styles.statusIcon} ${styles.error}`} aria-label="Error">✕</div>
            )}
            <div className={styles.feedEntryText}>{text}</div>
        </div>
    )
}
 
