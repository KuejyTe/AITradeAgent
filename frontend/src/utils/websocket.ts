type Listener<T> = (payload: T) => void

type WebSocketEvent = 'open' | 'close' | 'error' | 'message'

class WebSocketClient<TMessage = unknown> {
  private readonly url: string
  private ws: WebSocket | null = null
  private readonly reconnectInterval = 5000
  private readonly listeners: Map<WebSocketEvent, Listener<any>[]> = new Map()
  private reconnectTimer: number | null = null
  private manualClose = false

  constructor(url: string) {
    this.url = url
  }

  connect(): void {
    if (typeof window === 'undefined') {
      return
    }
    if (this.ws?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      this.ws = new window.WebSocket(this.url)

      this.ws.onopen = () => {
        this.emit('open', undefined)
      }

      this.ws.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data) as TMessage
          this.emit('message', data)
        } catch (error) {
          console.error('[WebSocketClient] Failed to parse message', error)
        }
      }

      this.ws.onerror = (event: Event) => {
        this.emit('error', event)
      }

      this.ws.onclose = () => {
        this.emit('close', undefined)
        if (!this.manualClose) {
          this.scheduleReconnect()
        }
      }
    } catch (error) {
      console.error('[WebSocketClient] Connection error', error)
      this.scheduleReconnect()
    }
  }

  private scheduleReconnect(): void {
    if (typeof window === 'undefined') {
      return
    }
    if (this.reconnectTimer) {
      window.clearTimeout(this.reconnectTimer)
    }
    this.reconnectTimer = window.setTimeout(() => {
      this.connect()
    }, this.reconnectInterval)
  }

  send(payload: unknown): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(payload))
    }
  }

  on<TPayload = TMessage>(event: WebSocketEvent, callback: Listener<TPayload>): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event)?.push(callback)
  }

  private emit<TPayload>(event: WebSocketEvent, payload: TPayload): void {
    const callbacks = this.listeners.get(event)
    callbacks?.forEach((callback) => callback(payload))
  }

  disconnect(): void {
    this.manualClose = true
    if (this.reconnectTimer) {
      window.clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}

export default WebSocketClient
