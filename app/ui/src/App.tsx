import "./App.css";
import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";

function App() {
  const [message, setMessage] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  
  // Mock data for the UI
  const [systemStatus] = useState({
    systemNormal: true,
    diagnosticsReady: true,
    activeFaults: 3,
    upcomingMaintenance: 2
  });
  
  const [userInput, setUserInput] = useState("");

  
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
      <div style={{ 
        padding: '24px', 
        maxWidth: '1400px', 
        margin: '0 auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '24px'
      }}>
        {/* Connection Status - Compact */}
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          gap: '12px', 
          padding: '12px 20px',
          backgroundColor: 'rgba(255, 255, 255, 0.05)',
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(10px)'
        }}>
          <div style={{
            width: '12px',
            height: '12px',
            borderRadius: '50%',
            backgroundColor: isConnected ? '#30D158' : '#FF453A',
            boxShadow: isConnected ? '0 0 8px rgba(48, 209, 88, 0.4)' : '0 0 8px rgba(255, 69, 58, 0.4)',
            animation: isChecking ? 'pulse 1s infinite' : 'none'
          }} />
          <span style={{ 
            color: isConnected ? '#30D158' : '#FF453A', 
            fontSize: '14px',
            fontWeight: '500'
          }}>
            {isConnected ? 'System Connected' : 'System Disconnected'}
          </span>
        </div>

        {/* Status Row - Compact Horizontal */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center',
          gap: '16px',
          flexWrap: 'wrap'
        }}>
          {[
            { 
              label: 'System Normal', 
              value: '', 
              color: '#30D158', 
              icon: '✓',
              bgColor: 'rgba(48, 209, 88, 0.1)'
            },
            { 
              label: 'Diagnostics Ready', 
              value: '', 
              color: '#007AFF', 
              icon: '⚙',
              bgColor: 'rgba(0, 122, 255, 0.1)'
            },
            { 
              label: 'Active Faults', 
              value: systemStatus.activeFaults, 
              color: '#FF453A', 
              icon: '!',
              bgColor: 'rgba(255, 69, 58, 0.1)'
            },
            { 
              label: 'Maintenance', 
              value: systemStatus.upcomingMaintenance, 
              color: '#FF9F0A', 
              icon: '🔧',
              bgColor: 'rgba(255, 159, 10, 0.1)'
            }
          ].map((status, index) => (
            <div
              key={index}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 16px',
                backgroundColor: status.bgColor,
                borderRadius: '20px',
                border: `1px solid ${status.color}20`,
                minWidth: '120px',
                justifyContent: 'center'
              }}
            >
              <div style={{
                width: '16px',
                height: '16px',
                borderRadius: '50%',
                backgroundColor: status.color,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '10px',
                color: '#fff'
              }}>
                {status.icon}
              </div>
              <span style={{ 
                color: '#fff', 
                fontSize: '13px',
                fontWeight: '500'
              }}>
                {status.label}
              </span>
              {status.value && (
                <span style={{ 
                  color: status.color, 
                  fontSize: '13px',
                  fontWeight: '600',
                  marginLeft: '4px'
                }}>
                  {status.value}
                </span>
              )}
            </div>
          ))}
        </div>

        {/* Main Dashboard Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '24px',
          alignItems: 'start'
        }}>
          {/* Left Column - Actions & Input */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '20px',
            height: '100%'
          }}>
            {/* Action Options */}
            <div>
              <h3 style={{ 
                color: '#fff', 
                marginBottom: '16px', 
                fontSize: '16px',
                fontWeight: '600',
                textAlign: 'center'
              }}>
                Diagnostic Actions
              </h3>
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(2, 1fr)', 
                gap: '12px' 
              }}>
                {[
                  { icon: '⚙', label: 'Run Diagnostics' },
                  { icon: '#', label: 'Search Error Code' },
                  { icon: '💡', label: 'Troubleshoot' },
                  { icon: '💬', label: 'Ask Question' }
                ].map((action, index) => (
                  <div
                    key={index}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      padding: '16px 12px',
                      backgroundColor: 'rgba(255, 255, 255, 0.05)',
                      borderRadius: '16px',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      backdropFilter: 'blur(10px)'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                      e.currentTarget.style.transform = 'translateY(-2px)';
                      e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.2)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.1)';
                    }}
                  >
                    <div style={{
                      fontSize: '20px',
                      marginBottom: '8px'
                    }}>
                      {action.icon}
                    </div>
                    <span style={{
                      color: '#fff',
                      fontSize: '11px',
                      textAlign: 'center',
                      lineHeight: '1.2',
                      fontWeight: '500'
                    }}>
                      {action.label}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Input Field - Positioned to align with results box */}
            <div style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column'
            }}>
              <h3 style={{ 
                color: '#fff', 
                marginBottom: '16px', 
                fontSize: '16px',
                fontWeight: '600',
                textAlign: 'center'
              }}>
                Diagnostic Input
              </h3>
              <div style={{
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
                borderRadius: '16px',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                padding: '20px',
                backdropFilter: 'blur(10px)',
                flex: 1,
                display: 'flex',
                flexDirection: 'column'
              }}>
                <input
                  type="text"
                  placeholder="Enter diagnostic question..."
                  value={userInput}
                  onChange={(e) => setUserInput(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    backgroundColor: 'rgba(0, 0, 0, 0.3)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    borderRadius: '12px',
                    color: '#fff',
                    fontSize: '14px',
                    outline: 'none',
                    boxSizing: 'border-box'
                  }}
                />
                <div style={{
                  marginTop: '12px',
                  color: 'rgba(255, 255, 255, 0.6)',
                  fontSize: '12px',
                  textAlign: 'center'
                }}>
                  Type your question and select an action
                </div>
              </div>
            </div>
          </div>

          {/* Right Column - Results */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            height: '100%'
          }}>
            <h3 style={{ 
              color: '#fff', 
              marginBottom: '16px', 
              fontSize: '16px',
              fontWeight: '600',
              textAlign: 'center'
            }}>
              Diagnostic Results
            </h3>
            <div style={{
              backgroundColor: 'rgba(255, 255, 255, 0.05)',
              borderRadius: '16px',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              padding: '24px',
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backdropFilter: 'blur(10px)'
            }}>
              <div style={{
                color: 'rgba(255, 255, 255, 0.5)',
                fontSize: '14px',
                textAlign: 'center',
                lineHeight: '1.5'
              }}>
                Diagnostic results will appear here<br />
                once you submit a query
              </div>
            </div>
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
