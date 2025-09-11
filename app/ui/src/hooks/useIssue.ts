import { useCallback, useEffect, useState } from "react";
import { invoke } from "@tauri-apps/api/core";

export function useIssue() {
  const [activeIssue, setActiveIssue] = useState(false);
  const [socket, setSocket] = useState<WebSocket | null>(null);

  const [issueLog, setIssueLog] = useState<any[]>([]);
  const [serverReady, setServerReady] = useState(false);
  const [loading, setLoading] = useState(false);
  const [thinking, setThinking] = useState<string>("");

  // no-op queue placeholder removed

  const enqueueIssueLog = useCallback((log: any) => {
    setIssueLog((prev) => [...prev, log]);
  }, []);

  const handleWebSocketMessage = useCallback((event: MessageEvent) => {
    console.log("WebSocket message received:", event.data);
    try {
      const data = JSON.parse(event.data);
      console.log("Parsed WebSocket data:", data);
      // handle special types for UI hints
      if (data.type === "diagnostics.loading") {
        setLoading(data.payload?.status === "started");
      } else if (data.type === "llm.thinking") {
        const text = data.payload?.text ?? "";
        setThinking((prev) => prev + String(text));
      } else {
        enqueueIssueLog(data);
      }
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

  const ensureSocketOpen = useCallback(async (): Promise<WebSocket | null> => {
    if (socket && socket.readyState === WebSocket.OPEN) return socket;
    try {
      const apiBase = (await invoke("api_base")) as string;
      const wsUrl = apiBase.replace("http", "ws") + "/issue/create";
      const ws = new WebSocket(wsUrl);
      return await new Promise<WebSocket | null>((resolve) => {
        ws.onopen = () => {
          setActiveIssue(true);
          setSocket(ws);
          resolve(ws);
        };
        ws.onmessage = handleWebSocketMessage;
        ws.onclose = () => {
          setActiveIssue(false);
          setSocket(null);
        };
        ws.onerror = (error) => {
          console.error("WebSocket error:", error);
          resolve(null);
        };
      });
    } catch (error) {
      console.error("Failed to open websocket:", error);
      return null;
    }
  }, [socket, handleWebSocketMessage]);

  const sendIssueBegin = useCallback(async (description: string) => {
    if (!description || description.trim().length === 0) return;
    let ws = socket;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      ws = await ensureSocketOpen();
      if (!ws) return;
      // Prompt the backend to greet the user
      ws.send(JSON.stringify({ type: "diagnostics.start" }));
    }
    const payload = {
      id: `issue_description`,
      name: "Issue Description",
      description: "Initial description provided by the user",
      rationale: "",
      outcomes: {},
      result: description,
    };
    ws.send(JSON.stringify({ type: "issue.begin", payload }));
  }, [socket, ensureSocketOpen]);

  const submitTestResult = useCallback(async (testId: string, result: any) => {
    if (!testId) return;
    let ws = socket;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      ws = await ensureSocketOpen();
      if (!ws) return;
    }
    ws.send(JSON.stringify({ type: "diagnostics.test_result", payload: { test_id: testId, result } }));
  }, [socket, ensureSocketOpen]);

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

  // Poll backend /test until available, then set serverReady
  useEffect(() => {
    let isActive = true;
    let timeoutId: number | undefined;

    const poll = async () => {
      try {
        const apiBase = (await invoke("api_base")) as string;
        const res = await fetch(apiBase + "/test", { method: "GET" });
        if (res.ok) {
          if (isActive) setServerReady(true);
          return;
        }
      } catch (e) {
        // ignore and retry
      }
      if (isActive) {
        timeoutId = window.setTimeout(poll, 1000);
      }
    };

    if (!serverReady) {
      poll();
    }

    return () => {
      isActive = false;
      if (timeoutId !== undefined) clearTimeout(timeoutId);
    };
  }, [serverReady]);






  return { activeIssue, createIssue, startDiagnostics, issueLog, serverReady, sendIssueBegin, submitTestResult, loading, thinking };
}



