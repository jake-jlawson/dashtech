import styles from "./FeedEntry.module.css";
import { useState } from "react";
import type { ReactElement } from "react";



export default function FeedEntry({log, onSubmitTestResult}: {log: any, onSubmitTestResult?: (testId: string, result: any) => void}) {
    
    const feedEntries: Record<string, ReactElement> = {
        "communications.talk": <TalkEntry log={log} />,
        "issue.created": <IssueCreatedEntry log={log} />,
        "diagnostics.test": <DiagnosticsTestEntry log={log} onSubmitTestResult={onSubmitTestResult} />,
    };
    
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
    const id = log?.payload?.issue_id;
    return (
        <div className={styles.flagRow}>
            <div className={styles.flagIcon}>✓</div>
            <div className={styles.flagText}>{id ? `Issue created (${id})` : "Issue created"}</div>
        </div>
    )
}

function DiagnosticsTestEntry({log, onSubmitTestResult}: {log: any, onSubmitTestResult?: (testId: string, result: any) => void}) {
    const payload = log?.payload || {};
    const testId: string = payload.test_id || payload.id;
    const testText: string = payload.test_text || payload.description || "";
    const rationale: string | undefined = payload.test_rationale || payload.rationale;
    const testInstructions: Array<{ step_number?: string | number, step_text: string }> = payload.test_instructions || [];
    const fieldLabel: string | undefined = payload.test_result_field_label;
    const fieldType: string | undefined = payload.test_result_field_type; // 'text' | 'number' | 'boolean' | 'array'
    const fieldOptions: string[] | undefined = payload.test_result_field_options;

    const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        if (!onSubmitTestResult || !testId) return;
        const formData = new FormData(e.currentTarget);
        let result: any = formData.get("result");
        if (fieldType === "number" && typeof result === "string") {
            const n = parseFloat(result);
            result = isNaN(n) ? null : n;
        }
        if (fieldType === "boolean" && typeof result === "string") {
            result = result === "true";
        }
        onSubmitTestResult(testId, result);
        e.currentTarget.reset();
    };

    return (
        <div className={styles.messageRow}>
            <div className={styles.agentAvatar}>🧪</div>
            <div className={styles.messageBubble}>
                {testText && <div className={styles.messageText}>{testText}</div>}
                {rationale && <div className={styles.messageSubtext}>Why: {rationale}</div>}
                {Array.isArray(testInstructions) && testInstructions.length > 0 && (
                    <ul className={styles.messageList}>
                        {testInstructions.map((step, idx) => (
                            <li key={idx}>{step.step_text}</li>
                        ))}
                    </ul>
                )}
                <form onSubmit={handleSubmit} className={styles.formRow}>
                    {fieldLabel && <label className={styles.formLabel}>{fieldLabel}</label>}
                    {fieldType === "text" && (
                        <input name="result" type="text" className={styles.formInput} />
                    )}
                    {fieldType === "number" && (
                        <input name="result" type="number" className={styles.formInput} />
                    )}
                    {fieldType === "boolean" && (
                        <select name="result" className={styles.formInput}>
                            <option value="true">Yes</option>
                            <option value="false">No</option>
                        </select>
                    )}
                    {fieldType === "array" && Array.isArray(fieldOptions) && fieldOptions.length > 0 && (
                        <select name="result" className={styles.formInput}>
                            {fieldOptions.map((opt: string, idx: number) => (
                                <option key={idx} value={opt}>{opt}</option>
                            ))}
                        </select>
                    )}
                    {!fieldType && (
                        <input name="result" type="text" className={styles.formInput} />
                    )}
                    <button type="submit" className={styles.formButton}>Submit</button>
                </form>
            </div>
        </div>
    );
}
