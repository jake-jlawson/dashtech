// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

// Imports
use tauri::{Manager, State};
use std::net::TcpListener;
use std::path::PathBuf;
use std::process::{Command, Stdio};


// Shared state for API base URL
struct ApiBase(String);

#[tauri::command]
fn api_base(base: State<ApiBase>) -> String { base.0.clone() }



// Pick DB path 
fn app_db_path(app: &tauri::AppHandle) -> PathBuf {
    let dir = app.path().app_data_dir().expect("app data dir");
    std::fs::create_dir_all(&dir).ok();
    dir.join("app.db")
}

// Pick a free port
fn pick_free_port() -> u16 {
    let listener = TcpListener::bind("127.0.0.1:0").expect("bind");
    let port = listener.local_addr().unwrap().port();
    drop(listener);
    port
}


// Spawn backend (dev)
// Spawn backend (dev)
fn spawn_backend_dev(app: &tauri::AppHandle, port: u16) {
    let db = app_db_path(app);
    
    // Get the current executable directory and navigate to project root
    let exe_dir = std::env::current_exe()
        .expect("Failed to get current executable path")
        .parent()
        .expect("Failed to get executable parent directory")
        .to_path_buf();
    
    // Navigate up from target/debug to project root
    let project_root = exe_dir
        .parent() // target
        .and_then(|p| p.parent()) // src-tauri
        .and_then(|p| p.parent()) // ui
        .and_then(|p| p.parent()) // app
        .and_then(|p| p.parent()) // project root
        .expect("Failed to find project root");
    
    let backend_dir = project_root.join("app").join("backend");
    let python_exe = if cfg!(target_os = "windows") {
        backend_dir.join("venv").join("Scripts").join("python.exe")
    } else {
        backend_dir.join("venv").join("bin").join("python")
    };
    
    println!("Attempting to start Python backend from: {:?}", backend_dir);
    println!("Using Python executable: {:?}", python_exe);
    
    let mut cmd = Command::new(&python_exe);
    cmd.current_dir(&backend_dir)
        .args(["-m", "api", "--port", &port.to_string(), "--db", db.to_str().unwrap()])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
        
    match cmd.spawn() {
        Ok(_child) => {
            println!("Successfully spawned Python backend on port {}", port);
        },
        Err(e) => {
            eprintln!("Failed to spawn Python backend with venv: {}", e);
            // Fallback to system python
            println!("Trying fallback with system Python...");
            let fallback_python = std::env::var("PYTHON").unwrap_or_else(|_| "python".to_string());
            match Command::new(&fallback_python)
                .current_dir(&backend_dir)
                .args(["-m", "api", "--port", &port.to_string(), "--db", db.to_str().unwrap()])
                .spawn() {
                Ok(_) => println!("Successfully spawned Python backend with system Python on port {}", port),
                Err(fallback_err) => {
                    eprintln!("Failed to spawn Python backend with system Python: {}", fallback_err);
                    eprintln!("Make sure Python is installed and the virtual environment is set up in: {:?}", backend_dir);
                }
            }
        }
    }
}



fn main() {
    tauri::Builder::default()
      .setup(|app| {
        let port = pick_free_port();
        let handle = app.handle().clone();
  
        // Spawn backend in development mode
        spawn_backend_dev(&handle, port);
  
        app.manage(ApiBase(format!("http://127.0.0.1:{port}")));
        Ok(())
      })
      .invoke_handler(tauri::generate_handler![api_base])
      .run(tauri::generate_context!())
      .expect("error while running tauri app");
}
