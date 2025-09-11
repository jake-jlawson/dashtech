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

fn find_python_executable(backend_dir: &str) -> String {
    // Prefer the project's virtual environment if present
    let venv_candidates = [
        PathBuf::from(backend_dir).join("venv").join("Scripts").join("python.exe"), // Windows
        PathBuf::from(backend_dir).join(".venv").join("Scripts").join("python.exe"), // Windows alt
        PathBuf::from(backend_dir).join("venv").join("bin").join("python3"),        // Unix
        PathBuf::from(backend_dir).join(".venv").join("bin").join("python3"),      // Unix alt
        PathBuf::from(backend_dir).join("venv").join("bin").join("python"),        // Unix fallback
        PathBuf::from(backend_dir).join(".venv").join("bin").join("python"),      // Unix fallback alt
    ];

    for venv_python in &venv_candidates {
        if venv_python.exists() {
            return venv_python.to_string_lossy().to_string();
        }
    }

    // Try common Python executable names on PATH; require a successful status
    let python_commands = ["py", "python3", "python"];
    for cmd in &python_commands {
        if let Ok(output) = Command::new(cmd).arg("--version").output() {
            if output.status.success() {
                return cmd.to_string();
            }
        }
    }

    // Final fallback
    "python".to_string()
}

fn find_backend_directory() -> String {
    // Collect candidate directories by walking up from current_dir and exe_dir
    let mut candidates: Vec<PathBuf> = Vec::new();

    if let Ok(current_dir) = env::current_dir() {
        for ancestor in current_dir.ancestors() {
            candidates.push(ancestor.join("app").join("backend"));
            candidates.push(ancestor.join("backend"));
        }
    }

    if let Ok(exe_dir) = std::env::current_exe() {
        if let Some(exe_parent) = exe_dir.parent() {
            for ancestor in exe_parent.ancestors() {
                candidates.push(ancestor.join("app").join("backend"));
                candidates.push(ancestor.join("backend"));
            }
        }
    }

    // Deduplicate simple duplicates while preserving order
    let mut seen = std::collections::HashSet::new();
    candidates.retain(|p| seen.insert(p.clone()));

    for path in candidates {
        if path.exists() && path.join("voice_recorder.py").exists() {
            println!("Found backend directory: {:?}", path);
            return path.to_string_lossy().to_string();
        }
    }

    // Final fallback - use current directory so caller can still attempt
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
    
    // Resolve backend directory, then choose Python interpreter
    let backend_dir = find_backend_directory();
    let python_cmd = find_python_executable(&backend_dir);
    
    // Call the Python voice recorder script with configurable duration
    let result = Command::new(python_cmd)
        .args(&["voice_recorder.py", "--duration", &duration_seconds.to_string(), "--model", "base"])
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
