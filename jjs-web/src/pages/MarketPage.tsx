import { Panel } from '@/components/Panel'

export function MarketPage() {
  return (
    <div className="h-full flex flex-col gap-3">
      <Panel title="股票详情" className="flex-1">
        <div className="p-10 text-center text-text-muted text-sm">
          选择一个股票查看详情和 K 线图
        </div>
      </Panel>
    </div>
  )
}
