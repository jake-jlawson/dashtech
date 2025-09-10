import "./App.css";
import { useState, useEffect, useRef } from "react";
import { invoke } from "@tauri-apps/api/core";

import StatusBadge from "./components/StatusBadge/StatusBadge";
import BackendConnectionStatus from "./components/BackendConnectionStatus/BackendConnectionStatus";
import Chat from "./screens/Chat/Chat";


function App() {
  return (
    <div className="appContainer">
      <div className="appHeader">
        
        <div className="backendConnectionStatus"><BackendConnectionStatus status="checking" /></div>

        <div className="statuses">
          {[
            { label: "System Normal", value: "", color: "#30D158", icon: "✓", bgColor: "rgba(48, 209, 88, 0.1)", active: true },
            { label: "Diagnostics Ready", value: "", color: "#007AFF", icon: "⚙", bgColor: "rgba(0, 122, 255, 0.1)", active: false },
            { label: "Active Faults", value: "", color: "#FF453A", icon: "!", bgColor: "rgba(255, 69, 58, 0.1)", active: false },
            { label: "Maintenance", value: "", color: "#FF9F0A", icon: "🔧", bgColor: "rgba(255, 159, 10, 0.1)", active: true }
          ]
          .sort((a, b) => a.active === b.active ? 0 : a.active ? -1 : 1)
          .map((badge, index) => (
            <StatusBadge 
              key={index}
              label={badge.label}
              value={badge.value}
              color={badge.color}
              icon={badge.icon}
              bgColor={badge.bgColor}
              active={badge.active}
            />
          ))}
        </div>
      </div>

      <div className="appContent">
        <Chat />
      </div>
    </div>
  )
}

export default App;