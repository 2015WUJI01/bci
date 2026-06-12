let ws = null;
let wsReconnectTimer = null;

function updateConnStatus(connected) {
  const el = document.getElementById('conn-status');
  const label = document.getElementById('conn-label');
  if (!el || !label) return;
  if (connected) {
    el.className = 'conn-status connected';
    label.textContent = '已连接';
  } else {
    el.className = 'conn-status disconnected';
    label.textContent = '未连接';
  }
}

function wsConnect(playerId, initialMsg) {
  if (ws) ws.close();
  if (wsReconnectTimer) clearTimeout(wsReconnectTimer);

  updateConnStatus(false);
  ws = new WebSocket(`${WS_URL}/ws?player_id=${playerId}`);

  ws.onopen = () => {
    console.log('WS connected');
    updateConnStatus(true);
    // Send initial message (e.g. join) immediately when connection opens
    if (initialMsg) {
      ws.send(JSON.stringify(initialMsg));
    }
  };

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      handleWsMessage(msg);
    } catch (e) {
      console.error('WS parse error', e);
    }
  };

  ws.onclose = () => {
    console.log('WS disconnected');
    updateConnStatus(false);
    wsReconnectTimer = setTimeout(() => {
      if (gameState.playerId) {
        wsConnect(gameState.playerId, initialMsg);
      }
    }, 3000);
  };

  ws.onerror = () => {
    console.error('WS error');
    updateConnStatus(false);
  };
}

function wsSend(type, data) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type, data }));
  }
}

// Heartbeat
window.heartbeatInterval = setInterval(() => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'ping' }));
  }
}, 30000);