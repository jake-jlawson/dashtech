use std::time::Duration;
use tokio::time::sleep;
use anyhow::Result;
use std::process::Command;
use std::path::PathBuf;
use std::env;

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

fn find_python_executable() -> String {
    // Try common Python executable names
    let python_commands = ["python3", "python", "py"];
    
    for cmd in &python_commands {
        if Command::new(cmd).arg("--version").output().is_ok() {
            return cmd.to_string();
        }
    }
    
    // Fallback to python3 if nothing else works
    "python3".to_string()
}

fn find_backend_directory() -> String {
    // Hardcoded path for now to ensure it works
    let backend_path = PathBuf::from("/Users/raghviarya/dashtech/app/backend");
    
    if backend_path.exists() && backend_path.join("voice_recorder.py").exists() {
        println!("Found backend directory: {:?}", backend_path);
        return backend_path.to_string_lossy().to_string();
    }
    
    // Try to find the backend directory relative to the current executable
    if let Ok(current_dir) = env::current_dir() {
        // Look for backend directory in common locations
        let possible_paths = [
            Some(current_dir.join("app").join("backend")),
            Some(current_dir.join("backend")),
            current_dir.parent().map(|p| p.join("app").join("backend")),
            current_dir.parent().map(|p| p.join("backend")),
        ];
        
        for path in possible_paths.iter().flatten() {
            if path.exists() && path.join("voice_recorder.py").exists() {
                println!("Found backend directory: {:?}", path);
                return path.to_string_lossy().to_string();
            }
        }
    }
    
    // Fallback: try to find from the project root
    if let Ok(current_dir) = env::current_dir() {
        // If we're in the ui directory, go up to find the backend
        if current_dir.ends_with("ui") || current_dir.ends_with("src-tauri") {
            let backend_path = current_dir
                .parent()
                .and_then(|p| p.parent())
                .map(|p| p.join("app").join("backend"));
            
            if let Some(path) = backend_path {
                if path.exists() && path.join("voice_recorder.py").exists() {
                    println!("Found backend directory from ui: {:?}", path);
                    return path.to_string_lossy().to_string();
                }
            }
        }
    }
    
    // Final fallback
    println!("Using fallback directory");
    env::current_dir()
        .unwrap_or_else(|_| PathBuf::from("."))
        .to_string_lossy()
        .to_string()
}

pub async fn record_and_transcribe() -> Result<String> {
    record_and_transcribe_with_duration(10).await
}

pub async fn record_and_transcribe_with_duration(duration_seconds: u32) -> Result<String> {
    println!("Starting real voice recording for {} seconds...", duration_seconds);
    
    // Find Python executable dynamically
    let python_cmd = find_python_executable();
    let backend_dir = find_backend_directory();
    
    // Call the Python voice recorder script with configurable duration
    let result = Command::new(python_cmd)
        .args(&["voice_recorder.py", "--duration", &duration_seconds.to_string(), "--model", "tiny"])
        .current_dir(&backend_dir)
        .output();
    
    match result {
        Ok(output) => {
            let stderr_output = String::from_utf8_lossy(&output.stderr);
            println!("Voice recording stderr: {}", stderr_output);
            
            if output.status.success() {
                let transcription = String::from_utf8_lossy(&output.stdout).trim().to_string();
                println!("Voice transcription: {}", transcription);
                
                if !transcription.is_empty() && !transcription.contains("No speech detected") {
                    Ok(transcription)
                } else {
                    Ok("No speech detected. Please try speaking louder or closer to the microphone.".to_string())
                }
            } else {
                let error = String::from_utf8_lossy(&output.stderr);
                println!("Voice recording error: {}", error);
                
                // Check for common error patterns and provide helpful messages
                if error.contains("Permission denied") || error.contains("microphone") {
                    Err(anyhow::anyhow!("Microphone permission denied. Please allow microphone access in your system settings and try again."))
                } else if error.contains("No module named") {
                    Err(anyhow::anyhow!("Missing Python dependencies. Please install required packages: pip install sounddevice openai-whisper numpy"))
                } else if error.contains("No such file or directory") {
                    Err(anyhow::anyhow!("Voice recording script not found. Please ensure the backend directory is properly set up."))
                } else {
                    Err(anyhow::anyhow!("Voice recording failed: {}", error))
                }
            }
        }
        Err(e) => {
            println!("Failed to run voice recorder: {}", e);
            if e.kind() == std::io::ErrorKind::NotFound {
                Err(anyhow::anyhow!("Python not found. Please ensure Python is installed and available in your PATH."))
            } else {
                Err(anyhow::anyhow!("Failed to run voice recorder: {}", e))
            }
        }
    }
}
