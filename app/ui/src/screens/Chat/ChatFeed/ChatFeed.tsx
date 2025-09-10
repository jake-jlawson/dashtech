

import styles from "./ChatFeed.module.css";
import {ServerActionEntry} from "../FeedEntries/FeedEntries";




export default function ChatFeed() {
    return (
        <div className={styles.chatFeed}>
            <div className={`${styles.chats}`}>
                <ServerActionEntry actionState="inProgress" text="Running diagnostics..." />
                <ServerActionEntry actionState="complete" text="Diagnostics completed." />
                <ServerActionEntry actionState="error" text="Diagnostics failed." />
            </div>
        </div>
    )
}