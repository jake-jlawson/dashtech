import "./App.css";
import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";

function App() {
  const [message, setMessage] = useState("");
  const [isConnected, setIsConnected] = useState(false);

  
  const api_test = async () => {
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
    }
  };


  useEffect(() => {
    api_test();
  }, []);

  return (
    <main className="container">
      <div>
        <p>{message}</p>
      </div>
    </main>
  );
}

export default App;
