import type { LightbulbIcon as LucideProps } from "lucide-react"

export function ChartBarIcon(props: LucideProps) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect width="18" height="18" x="3" y="3" rx="2" />
      <line x1="9" x2="9" y1="9" y2="15" />
      <line x1="15" x2="15" y1="6" y2="15" />
    </svg>
  )
}
