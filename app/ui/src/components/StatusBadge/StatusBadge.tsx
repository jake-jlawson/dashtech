

import styles from "./StatusBadge.module.css";


interface StatusBadgeProps {
  label: string;
  value?: string | number;
  color: string;
  icon: string;
  bgColor: string;
  active?: boolean;
}


export default function StatusBadge({ label, value, color, icon, bgColor, active = true }: StatusBadgeProps) {
  return (
    <div className={`${styles.statusButton}`} style={{
        backgroundColor: bgColor,
        borderColor: color,
        opacity: active ? 1 : 0.55,
        filter: active ? 'none' : 'saturate(70%) brightness(0.9)'
    }}>
        <div className={`${styles.icon}`} style={{backgroundColor: color, opacity: active ? 1 : 0.8}}>
            {icon}
        </div>

        <span className={`${styles.label}`} style={{opacity: active ? 1 : 0.85}}>{label}</span>

        {value && (
            <span className={`${styles.label}`} style={{marginLeft: '4px', opacity: active ? 1 : 0.85}}>{value}</span>
        )}
    </div>
  )
}
