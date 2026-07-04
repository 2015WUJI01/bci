import { useState, useCallback, useEffect, createContext, useContext, type ReactNode } from 'react'

interface ToastItem {
  id: number
  message: string
  type: 'error' | 'success' | 'info'
}

interface ToastContextValue {
  toast: (message: string, type?: 'error' | 'success' | 'info') => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

let nextId = 0

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([])

  const toast = useCallback((message: string, type: 'error' | 'success' | 'info' = 'error') => {
    const id = nextId++
    setItems((prev) => [...prev, { id, message, type }])
  }, [])

  const remove = useCallback((id: number) => {
    setItems((prev) => prev.filter((t) => t.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
        {items.map((t) => (
          <ToastItem key={t.id} item={t} onDone={remove} />
        ))}
      </div>
    </ToastContext.Provider>
  )
}

function ToastItem({ item, onDone }: { item: ToastItem; onDone: (id: number) => void }) {
  useEffect(() => {
    const timer = setTimeout(() => onDone(item.id), 3000)
    return () => clearTimeout(timer)
  }, [item.id, onDone])

  const bg = item.type === 'error' ? 'bg-down/20 border-down text-down'
    : item.type === 'success' ? 'bg-up/20 border-up text-up'
    : 'bg-accent-blue/20 border-accent-blue text-accent-blue'

  return (
    <div className={`px-4 py-2.5 rounded border text-xs font-medium shadow-lg animate-in slide-in-from-right ${bg}`}>
      {item.message}
    </div>
  )
}

export function useToast(): (message: string, type?: 'error' | 'success' | 'info') => void {
  const ctx = useContext(ToastContext)
  if (!ctx) {
    return () => {}
  }
  return ctx.toast
}
