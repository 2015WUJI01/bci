interface PanelProps {
  title: string
  children: React.ReactNode
  className?: string
  headerAction?: React.ReactNode
}

export function Panel({ title, children, className = '', headerAction }: PanelProps) {
  return (
    <div
      className={`bg-bg-card rounded border border-border shadow-sm hover:border-border-light transition-colors overflow-hidden ${className}`}
    >
      <div className="flex items-center justify-between px-3.5 py-2.5 text-xs font-bold text-text-secondary border-b border-border bg-[linear-gradient(180deg,rgba(255,255,255,0.03),transparent)] tracking-wider">
        <span>{title}</span>
        {headerAction}
      </div>
      {children}
    </div>
  )
}
