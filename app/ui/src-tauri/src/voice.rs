use std::time::Duration;
use tokio::time::sleep;
use anyhow::Result;
use std::process::Command;

pub struct VoiceRecorder {
    // Simplified struct for testing
}

impl VoiceRecorder {
    pub fn new() -> Result<Self> {
        Ok(VoiceRecorder {})
    }

    pub async fn start_recording(&self) -> Result<()> {
        // For now, we'll use a simplified approach that doesn't require Send
        // This simulates recording for 5 seconds
        println!("Starting voice recording simulation...");
        sleep(Duration::from_secs(5)).await;
        println!("Voice recording simulation completed.");
        Ok(())
    }

}

pub async fn record_and_transcribe() -> Result<String> {
    record_and_transcribe_with_duration(5).await
}

pub async fn record_and_transcribe_with_duration(duration_seconds: u32) -> Result<String> {
    println!("Starting real voice recording for {} seconds...", duration_seconds);
    
    // Call the Python voice recorder script with configurable duration
    let result = Command::new("/Users/raghviarya/.pyenv/versions/3.11.9/bin/python")
        .args(&["voice_recorder.py", "--duration", &duration_seconds.to_string(), "--model", "tiny"])
        .current_dir("/Users/raghviarya/dashtech/app/backend") // Navigate to backend directory
        .output();
    
    match result {
        Ok(output) => {
            if output.status.success() {
                let transcription = String::from_utf8_lossy(&output.stdout).trim().to_string();
                let stderr_output = String::from_utf8_lossy(&output.stderr);
                
                println!("Voice recording stderr: {}", stderr_output);
                println!("Voice transcription: {}", transcription);
                
                if !transcription.is_empty() {
                    Ok(transcription)
                } else {
                    Ok("No speech detected. Please try speaking louder or closer to the microphone.".to_string())
                }
            } else {
                let error = String::from_utf8_lossy(&output.stderr);
                println!("Voice recording error: {}", error);
                Err(anyhow::anyhow!("Voice recording failed: {}", error))
            }
        }
        Err(e) => {
            println!("Failed to run voice recorder: {}", e);
            Err(anyhow::anyhow!("Failed to run voice recorder: {}", e))
        }
    }
}
