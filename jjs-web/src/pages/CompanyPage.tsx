import { Panel } from '@/components/Panel'

export function CompanyPage() {
  return (
    <div className="h-full flex flex-col items-center justify-center">
      <Panel title="公司经营" className="w-full max-w-lg">
        <div className="p-10 text-center space-y-3">
          <span className="text-3xl block">🏢</span>
          <p className="text-text-muted text-sm">公司系统即将开放</p>
        </div>
      </Panel>
    </div>
  )
}
