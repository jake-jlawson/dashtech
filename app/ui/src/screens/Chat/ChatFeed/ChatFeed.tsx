

import styles from "./ChatFeed.module.css";
import {ServerActionEntry} from "../FeedEntries/FeedEntries";
import FeedEntry from "../FeedEntries/FeedEntry";


interface ChatFeedProps {
    issueLog: any[];
}

export default function ChatFeed({issueLog}: ChatFeedProps) {
    return (
        <div className={styles.chatFeed}>
            <div className={`${styles.chats}`}>
                {issueLog && issueLog.map((log, index) => (
                    <FeedEntry key={index} log={log} />
                ))}
            </div>
            
        </div>
    )
}