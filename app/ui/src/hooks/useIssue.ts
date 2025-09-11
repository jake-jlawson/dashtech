import { useCallback, useEffect, useState } from "react";
import { invoke } from "@tauri-apps/api/core";

export function useIssue() {
  const [activeIssue, setActiveIssue] = useState(false);
  const [socket, setSocket] = useState<WebSocket | null>(null);

  const [issueLog, setIssueLog] = useState<any[]>([]);

  const enqueueIssueLog = useCallback((log: any) => {
    setIssueLog((prev) => [...prev, log]);
  }, []);

  const handleWebSocketMessage = useCallback((event: MessageEvent) => {
    console.log("WebSocket message received:", event.data);
    try {
      const data = JSON.parse(event.data);
      console.log("Parsed WebSocket data:", data);
      enqueueIssueLog(data);
    } catch (error) {
      console.log("Raw WebSocket data (not JSON):", event.data);
      enqueueIssueLog({ type: "raw", payload: String(event.data) });
    }
  }, [enqueueIssueLog]);

  const createIssue = useCallback(async () => {
    try {
      const apiBase = (await invoke("api_base")) as string;
      const wsUrl = apiBase.replace("http", "ws") + "/issue/create";

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setActiveIssue(true);
        setSocket(ws);
        console.log("WebSocket connected");
      };

      ws.onmessage = handleWebSocketMessage;

      ws.onclose = () => {
        setActiveIssue(false);
        setSocket(null);
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
      };

    } catch (error) {
      console.error("Failed to create issue:", error);
    }
  }, [handleWebSocketMessage]);

  const startDiagnostics = useCallback(async () => {
    try {
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: "diagnostics.start" }));
        return;
      }

      const apiBase = (await invoke("api_base")) as string;
      const wsUrl = apiBase.replace("http", "ws") + "/issue/create";
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setActiveIssue(true);
        setSocket(ws);
        ws.send(JSON.stringify({ type: "diagnostics.start" }));
      };

      ws.onmessage = handleWebSocketMessage;

      ws.onclose = () => {
        setActiveIssue(false);
        setSocket(null);
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
      };
    } catch (error) {
      console.error("Failed to start diagnostics:", error);
    }
  }, [socket, handleWebSocketMessage]);

  useEffect(() => {
    return () => {
      if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
        try {
          socket.close();
        } catch (e) {
          // ignore
        }
      }
    };
  }, [socket]);

  return { activeIssue, createIssue, startDiagnostics, issueLog };
}
