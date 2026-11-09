import { useEffect, useState } from 'react'
import './App.css'

type ConnectionState = 'checking' | 'connected' | 'database-unavailable' | 'offline'

type HealthResponse = {
  data: { status: 'ok'; database: 'ok' }
  meta: { request_id: string }
}

const copy: Record<ConnectionState, { title: string; detail: string }> = {
  checking: { title: '正在检查学习工作台', detail: '请稍等，正在连接本机服务。' },
  connected: { title: '学习工作台已就绪', detail: '服务与学习记录均可正常使用。' },
  'database-unavailable': { title: '学习记录暂时无法读取', detail: '本机服务已启动，数据库需要检查。' },
  offline: { title: '暂时无法连接学习工作台', detail: '请确认本机服务已启动，然后重试。' },
}

function App() {
  const [connection, setConnection] = useState<ConnectionState>('checking')
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()

    async function checkHealth() {
      setConnection('checking')
      try {
        const response = await fetch('/api/v1/health', { signal: controller.signal })
        if (response.status === 503) {
          setConnection('database-unavailable')
          return
        }
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        const result = (await response.json()) as HealthResponse
        setConnection(result.data.status === 'ok' && result.data.database === 'ok' ? 'connected' : 'database-unavailable')
      } catch {
        if (!controller.signal.aborted) setConnection('offline')
      }
    }

    void checkHealth()
    return () => controller.abort()
  }, [attempt])

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand-mark">期</div>
        <div className="brand-name">期末复习</div>
        <p className="brand-caption">你的学习工作台</p>
      </aside>

      <section className="content" aria-live="polite">
        <div className="status-card">
          <span className={`status-dot ${connection}`} aria-hidden="true" />
          <p className="eyebrow">服务状态</p>
          <h1>{copy[connection].title}</h1>
          <p className="description">{copy[connection].detail}</p>
          <div className="status-row">
            <span>本机服务</span>
            <strong>{connection === 'connected' || connection === 'database-unavailable' ? '已连接' : connection === 'checking' ? '检查中' : '未连接'}</strong>
          </div>
          <div className="status-row">
            <span>学习记录</span>
            <strong>{connection === 'connected' ? '可用' : connection === 'checking' ? '检查中' : '暂不可用'}</strong>
          </div>
          <button type="button" onClick={() => setAttempt(value => value + 1)} disabled={connection === 'checking'}>
            重新检查
          </button>
        </div>
      </section>
    </main>
  )
}

export default App
