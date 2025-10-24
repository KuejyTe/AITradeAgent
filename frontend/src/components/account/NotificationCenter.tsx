import { useMemo, useState } from 'react'
import { useAccount } from '../../context/AccountContext'
import { Notification } from '../../types/account'
import { formatDateTime } from '../../utils/format'

const CATEGORY_LABELS: Record<Notification['category'], string> = {
  order: '订单',
  price: '价格',
  strategy: '策略',
  system: '系统',
}

const NotificationCenter: React.FC = () => {
  const { notifications, markNotificationRead, clearNotifications } = useAccount()
  const [category, setCategory] = useState<'ALL' | Notification['category']>('ALL')

  const filtered = useMemo(
    () =>
      notifications.filter((item) => (category === 'ALL' ? true : item.category === category)),
    [notifications, category],
  )

  const markAllAsRead = () => {
    notifications.filter((item) => !item.read).forEach((item) => markNotificationRead(item.id))
  }

  return (
    <section className="card notification-center">
      <header className="card-header">
        <div>
          <h2>通知中心</h2>
          <p>订单、价格、策略与系统告警实时汇总</p>
        </div>
        <div className="actions">
          <button className="secondary" onClick={markAllAsRead}>
            全部标记为已读
          </button>
          <button className="secondary" onClick={() => clearNotifications()}>
            清空通知
          </button>
        </div>
      </header>

      <div className="filter-tabs">
        <button className={category === 'ALL' ? 'active' : ''} onClick={() => setCategory('ALL')}>
          全部
        </button>
        {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
          <button key={key} className={category === key ? 'active' : ''} onClick={() => setCategory(key as Notification['category'])}>
            {label}
          </button>
        ))}
      </div>

      <ul className="notification-list">
        {filtered.map((notification) => (
          <li key={notification.id} className={`${notification.read ? 'read' : 'unread'} severity-${notification.severity}`}>
            <div className="notification-header">
              <span className="badge">{CATEGORY_LABELS[notification.category]}</span>
              <time>{formatDateTime(notification.timestamp)}</time>
            </div>
            <div className="notification-body">
              <h4>{notification.title}</h4>
              <p>{notification.message}</p>
            </div>
            {!notification.read ? (
              <button className="link-button" onClick={() => markNotificationRead(notification.id)}>
                标记为已读
              </button>
            ) : null}
          </li>
        ))}
        {!filtered.length ? <li className="empty">暂无通知</li> : null}
      </ul>
    </section>
  )
}

export default NotificationCenter
