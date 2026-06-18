import { Panel } from '@/components/Panel'

export function PortfolioPage() {
  return (
    <div className="h-full flex flex-col gap-3">
      <Panel title="持仓" className="flex-1">
        <div className="p-8 text-center text-text-muted text-sm">
          暂无持仓
        </div>
      </Panel>
    </div>
  )
}
