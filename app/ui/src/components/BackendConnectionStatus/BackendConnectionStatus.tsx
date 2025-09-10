

import styles from "./BackendConnectionStatus.module.css";

type status = "connected" | "disconnected" | "checking";

export default function BackendConnectionStatus({ status }: { status: status }) {
  const dotStylesMap = {
    connected: {
      backgroundColor: "#30D158",
      boxShadow: "0 0 8px rgba(48, 209, 88, 0.4)",
    },
    disconnected: {
      backgroundColor: "#FF453A",
      boxShadow: "0 0 8px rgba(255, 69, 58, 0.4)",
    },
    checking: {
      backgroundColor: "#FF9F0A",
      boxShadow: "0 0 8px rgba(255, 159, 10, 0.4)",
      animation: "pulse 1s infinite",
    },
  } as const;

  const textColorMap = {
    connected: "#30D158",
    disconnected: "#FF453A",
    checking: "#FF9F0A",
  } as const;

  const label =
    status === "connected"
      ? "System Connected"
      : status === "disconnected"
      ? "Can't connect to backend"
      : "System Checking";

  return (
    <div className={styles.backendConnectionStatus}>
      <div className={styles.statusDot} style={dotStylesMap[status]} />
      <span className={styles.statusText} style={{ color: textColorMap[status] }}>
        {label}
      </span>
    </div>
  );
}