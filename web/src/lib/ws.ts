import { useAppStore } from "./store";

const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL ??
  `ws://localhost:8000/ws`;

const MIN_DELAY = 1000;
const MAX_DELAY = 30000;

let ws: WebSocket | null = null;
let reconnectDelay = MIN_DELAY;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let stopped = false;

function onMessage(event: MessageEvent) {
  try {
    const data = JSON.parse(event.data);
    const store = useAppStore.getState();

    if (data.type === "session.state") {
      store.updateProjectState(data.project_id, data.state, {
        startedAt: data.started_at ?? null,
        url: data.url ?? undefined,
      });
    } else if (data.type === "project.list_changed") {
      store.loadProjects();
    }
  } catch {
    // ignore malformed messages
  }
}

function connect() {
  if (stopped) return;

  const store = useAppStore.getState();
  store.setConnectionStatus("connecting");

  ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    reconnectDelay = MIN_DELAY;
    useAppStore.getState().setConnectionStatus("connected");
    // Reload projects on reconnect to sync state
    useAppStore.getState().loadProjects();
  };

  ws.onmessage = onMessage;

  ws.onclose = () => {
    ws = null;
    useAppStore.getState().setConnectionStatus("disconnected");
    scheduleReconnect();
  };

  ws.onerror = () => {
    // onclose will fire after this
  };
}

function scheduleReconnect() {
  if (stopped) return;
  if (reconnectTimer) return;

  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    reconnectDelay = Math.min(reconnectDelay * 2, MAX_DELAY);
    connect();
  }, reconnectDelay);
}

export function startWebSocket() {
  stopped = false;
  if (!ws) connect();
}

export function stopWebSocket() {
  stopped = true;
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  if (ws) {
    ws.close();
    ws = null;
  }
}
