import { Panel } from '@/components/Panel'

export function TradePage() {
  return (
    <div className="h-full flex flex-col gap-3">
      <Panel title="交易" className="flex-1">
        <div className="p-10 text-center text-text-muted text-sm">
          交易面板（P7 阶段实现）
        </div>
      </Panel>
    </div>
  )
}
