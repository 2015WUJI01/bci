import { Panel } from '@/components/Panel'

export function LeaderboardPage() {
  return (
    <div className="h-full flex flex-col gap-3">
      <Panel title="排行榜" className="flex-1">
        <div className="p-8 text-center text-text-muted text-sm">
          加载中...
        </div>
      </Panel>
    </div>
  )
}
