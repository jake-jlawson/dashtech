import "./App.css";
import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";

function App() {
  const [message, setMessage] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [isChecking, setIsChecking] = useState(false);

  
  const api_test = async () => {
    setIsChecking(true);
    try {
      
      const api_base = await invoke("api_base");
      console.log("base: ", api_base);
      const response = await fetch(`${api_base}/test`);
      
      if (response.ok) {
        const data = await response.json();
        setMessage(`Dashtech is successfully connected to the backend. Message from backend: ${data.message}`);
        setIsConnected(true);
      } else {
        throw new Error("Failed to connect");
      }
    } catch (error) {
      console.error("error: ", error);
      setMessage("Dashtech cannot find backend");
      setIsConnected(false);
    } finally {
      setIsChecking(false);
    }
  };


  useEffect(() => {
    // Initial check
    api_test();
    
    // Set up interval to check every 5 seconds
    const interval = setInterval(() => {
      api_test();
    }, 5000);

    // Cleanup interval on component unmount
    return () => clearInterval(interval);
  }, []);

  return (
    <main className="container">
      <div style={{ padding: '20px' }}>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '10px', 
          marginBottom: '20px',
          padding: '15px',
          border: '1px solid #ddd',
          borderRadius: '8px',
          backgroundColor: '#f9f9f9'
        }}>
          <div style={{
            width: '20px',
            height: '20px',
            borderRadius: '50%',
            backgroundColor: isConnected ? '#4CAF50' : '#f44336',
            boxShadow: isConnected ? '0 0 10px rgba(76, 175, 80, 0.5)' : '0 0 10px rgba(244, 67, 54, 0.5)',
            animation: isChecking ? 'pulse 1s infinite' : 'none'
          }} />
          <div>
            <h3 style={{ margin: '0 0 5px 0', color: isConnected ? '#4CAF50' : '#f44336' }}>
              {isConnected ? 'Connected to Backend' : 'Not Connected to Backend'}
            </h3>
            <p style={{ margin: 0, fontSize: '14px', color: '#666' }}>
              {isChecking ? 'Checking connection...' : message}
            </p>
          </div>
        </div>
      </div>
      <style>{`
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.5; }
          100% { opacity: 1; }
        }
      `}</style>
    </main>
  );
}

export default App;
