function formatMoney(val) {
  return '¥' + Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function formatNumber(val) {
  return Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatAmountCN(val) {
  if (val == null || isNaN(val)) return '¥0';
  var v = Number(val);
  var absV = Math.abs(v);
  if (absV >= 100000000) return (v / 100000000).toFixed(2) + '亿';
  if (absV >= 10000) return (v / 10000).toFixed(2) + '万';
  return '¥' + v.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatPercent(val) {
  const sign = val >= 0 ? '+' : '';
  return sign + val.toFixed(2) + '%';
}

function formatTime(seconds) {
  if (seconds == null || seconds < 0) return '--:--';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return m.toString().padStart(2, '0') + ':' + s.toString().padStart(2, '0');
}

function priceClass(change) {
  if (change > 0) return 'price-up';
  if (change < 0) return 'price-down';
  return '';
}

function showToast(msg, type) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'toast' + (type ? ' ' + type : '');
  el.classList.remove('hidden');
  setTimeout(() => el.classList.add('hidden'), 2500);
}

const WS_PROTO = location.protocol === 'https:' ? 'wss:' : 'ws:';
const WS_URL = `${WS_PROTO}//${location.host}`;
const API_URL = `${location.protocol}//${location.host}`;
