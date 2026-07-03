import { useState } from 'react'
import { usePlayerLeaderboard, useCompanyLeaderboard } from '@/api/queries'
import { useAuthStore } from '@/stores/authStore'
import { Panel } from '@/components/Panel'
import type { PlayerLeaderboardEntry, CompanyLeaderboardEntry } from '@/types'

const INDUSTRY_NAME: Record<string, string> = {
  tech: '科技',
  finance: '金融',
  manufacturing: '制造',
  mining: '矿业',
  consumer: '消费',
  healthcare: '医疗',
}

type Tab = 'players' | 'companies'

function RankBadge({ rank }: { rank: number }) {
  if (rank === 1) return <span className="text-lg">🥇</span>
  if (rank === 2) return <span className="text-lg">🥈</span>
  if (rank === 3) return <span className="text-lg">🥉</span>
  return <span className="text-text-muted tabular-nums w-6 text-center">{rank}</span>
}

function RankRowClass(rank: number) {
  if (rank === 1) return 'bg-amber-500/10'
  if (rank === 2) return 'bg-slate-400/10'
  if (rank === 3) return 'bg-amber-700/10'
  return ''
}

export function LeaderboardPage() {
  const [tab, setTab] = useState<Tab>('players')
  const playerId = useAuthStore((s) => s.playerId)

  const players = usePlayerLeaderboard()
  const companies = useCompanyLeaderboard()

  const tabs = (
    <div className="flex gap-0.5">
      <button
        onClick={() => setTab('players')}
        className={`px-3 py-1 text-xs font-semibold rounded transition-colors ${
          tab === 'players'
            ? 'bg-accent-blue/20 text-accent-blue'
            : 'text-text-muted hover:text-text-secondary'
        }`}
      >
        个人排行
      </button>
      <button
        onClick={() => setTab('companies')}
        className={`px-3 py-1 text-xs font-semibold rounded transition-colors ${
          tab === 'companies'
            ? 'bg-accent-blue/20 text-accent-blue'
            : 'text-text-muted hover:text-text-secondary'
        }`}
      >
        公司排行
      </button>
    </div>
  )

  return (
    <div className="h-full flex flex-col gap-3">
      <Panel title="排行榜" headerAction={tabs} className="flex-1">
        {tab === 'players' ? (
          <PlayerLeaderboard data={players} playerId={playerId} />
        ) : (
          <CompanyLeaderboard data={companies} />
        )}
      </Panel>
    </div>
  )
}

function PlayerLeaderboard({
  data,
  playerId,
}: {
  data: ReturnType<typeof usePlayerLeaderboard>
  playerId: string | null
}) {
  if (data.isLoading) {
    return <LoadingState />
  }
  if (data.isError) {
    return <ErrorState />
  }
  const list = data.data?.players ?? []
  if (list.length === 0) {
    return <EmptyState />
  }

  return (
    <div className="overflow-y-auto max-h-[calc(100vh-12rem)]">
      <table className="w-full text-sm">
        <thead className="sticky top-0 z-10">
          <tr className="bg-bg-card text-text-muted text-xs">
            <th className="py-2.5 px-3 text-left w-14">#</th>
            <th className="py-2.5 px-3 text-left">昵称</th>
            <th className="py-2.5 px-3 text-right">总资产</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border/50">
          {list.map((entry) => (
            <PlayerRow key={entry.player_id} entry={entry} isMe={entry.player_id === playerId} />
          ))}
        </tbody>
      </table>
    </div>
  )
}

function PlayerRow({ entry, isMe }: { entry: PlayerLeaderboardEntry; isMe: boolean }) {
  return (
    <tr
      className={`transition-colors ${RankRowClass(entry.rank)} ${
        isMe ? 'border-l-2 border-l-accent-blue bg-accent-blue/5' : ''
      }`}
    >
      <td className="py-2 px-3">
        <RankBadge rank={entry.rank} />
      </td>
      <td className="py-2 px-3">
        <span className={isMe ? 'text-accent-blue font-semibold' : 'text-text-primary'}>
          {entry.nickname || `玩家${entry.player_id.slice(0, 4)}`}
        </span>
      </td>
      <td className="py-2 px-3 text-right tabular-nums text-text-primary font-semibold">
        ¥{entry.total_assets.toLocaleString()}
      </td>
    </tr>
  )
}

function CompanyLeaderboard({
  data,
}: {
  data: ReturnType<typeof useCompanyLeaderboard>
}) {
  if (data.isLoading) {
    return <LoadingState />
  }
  if (data.isError) {
    return <ErrorState />
  }
  const list = data.data?.companies ?? []
  if (list.length === 0) {
    return <EmptyState />
  }

  return (
    <div className="overflow-y-auto max-h-[calc(100vh-12rem)]">
      <table className="w-full text-sm">
        <thead className="sticky top-0 z-10">
          <tr className="bg-bg-card text-text-muted text-xs">
            <th className="py-2.5 px-3 text-left w-14">#</th>
            <th className="py-2.5 px-3 text-left">公司</th>
            <th className="py-2.5 px-3 text-left hidden sm:table-cell">行业</th>
            <th className="py-2.5 px-3 text-right">估值</th>
            <th className="py-2.5 px-3 text-right hidden sm:table-cell">股价</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border/50">
          {list.map((entry) => (
            <CompanyRow key={entry.symbol} entry={entry} />
          ))}
        </tbody>
      </table>
    </div>
  )
}

function CompanyRow({ entry }: { entry: CompanyLeaderboardEntry }) {
  return (
    <tr className={`transition-colors ${RankRowClass(entry.rank)}`}>
      <td className="py-2 px-3">
        <RankBadge rank={entry.rank} />
      </td>
      <td className="py-2 px-3">
        <div className="flex flex-col">
          <span className="text-accent-blue font-mono text-xs">{entry.symbol}</span>
          <span className="text-text-primary text-sm">{entry.name}</span>
        </div>
      </td>
      <td className="py-2 px-3 hidden sm:table-cell">
        <span className="text-text-secondary text-xs px-1.5 py-0.5 rounded bg-white/5">
          {INDUSTRY_NAME[entry.industry] ?? entry.industry}
        </span>
      </td>
      <td className="py-2 px-3 text-right tabular-nums text-text-primary font-semibold">
        ¥{Math.round(entry.valuation).toLocaleString()}
      </td>
      <td className="py-2 px-3 text-right tabular-nums hidden sm:table-cell">
        {entry.listed ? (
          <span className="text-text-primary">¥{entry.stock_price.toFixed(2)}</span>
        ) : (
          <span className="text-text-muted text-xs">未上市</span>
        )}
      </td>
    </tr>
  )
}

function LoadingState() {
  return (
    <div className="p-8 text-center text-text-muted text-sm">
      <div className="flex flex-col gap-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-8 bg-white/5 rounded animate-pulse" />
        ))}
      </div>
    </div>
  )
}

function ErrorState() {
  return (
    <div className="p-8 text-center text-text-muted text-sm">
      加载失败，请稍后重试
    </div>
  )
}

function EmptyState() {
  return (
    <div className="p-8 text-center text-text-muted text-sm">
      暂无排行数据
    </div>
  )
}
