// ============================================================
// K-line (Candlestick) Chart — lightweight-charts v5
// ============================================================

const KLINE = {
  UP_COLOR: '#ef4444',
  DOWN_COLOR: '#22c55e',
  GRID_COLOR: '#1a2c38',
  TEXT_COLOR: '#5a7a8a',
};

let klineData = [];
let dailyData = [];
let weeklyData = [];
let monthlyData = [];
let currentIndicator = 'MACD';
let displayPeriod = 'kline-4t';
let showTimeshare = false;
let timeshareData = [];

let chart = null;
let candleSeries = null;
let volumeSeries = null;
let _indicatorLines = [];
let _currentPane = 'main';

function initChart() {
  if (chart) return;
  var container = document.getElementById('kline-canvas');
  if (!container) return;
  // lightweight-charts uses the canvas element directly
  chart = LightweightCharts.createChart(container, {
    layout: {
      background: { type: 'solid', color: '#0a0e17' },
      textColor: '#5a7a8a',
      fontSize: 11,
    },
    grid: {
      vertLines: { color: '#1a2c38' },
      horzLines: { color: '#1a2c38' },
    },
    crosshair: {
      mode: LightweightCharts.CrosshairMode.Normal,
      vertLine: { color: '#8a9ba8', width: 1, style: LightweightCharts.LineStyle.Dashed, labelBackgroundColor: '#1a2332' },
      horzLine: { color: '#8a9ba8', width: 1, style: LightweightCharts.LineStyle.Dashed, labelBackgroundColor: '#1a2332' },
    },
    timeScale: {
      borderColor: '#2a4050',
      timeVisible: true,
      secondsVisible: false,
      fixLeftEdge: true,
      fixRightEdge: true,
    },
    rightPriceScale: {
      borderColor: '#2a4050',
    },
  });

  candleSeries = chart.addCandlestickSeries({
    upColor: KLINE.UP_COLOR,
    downColor: KLINE.DOWN_COLOR,
    borderUpColor: KLINE.UP_COLOR,
    borderDownColor: KLINE.DOWN_COLOR,
    wickUpColor: KLINE.UP_COLOR,
    wickDownColor: KLINE.DOWN_COLOR,
  });

  volumeSeries = chart.addHistogramSeries({
    priceFormat: { type: 'volume' },
    priceScaleId: 'volume',
  });
  chart.priceScale('volume').applyOptions({
    scaleMargins: { top: 0.8, bottom: 0 },
  });

  // Handle resize
  var observer = new ResizeObserver(function() {
    if (chart) chart.resize(container.clientWidth, container.clientHeight);
  });
  observer.observe(container);
}

// Convert our candle data to lightweight-charts format
function _toLC(candles) {
  if (!candles || !candles.length) return [];
  return candles.map(function(c) {
    return {
      time: Math.floor(c.time / 1000),
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    };
  });
}

function _volumeData(candles) {
  if (!candles || !candles.length) return [];
  return candles.map(function(c) {
    var isUp = c.close >= c.open;
    return {
      time: Math.floor(c.time / 1000),
      value: c.volume || 0,
      color: isUp ? KLINE.UP_COLOR : KLINE.DOWN_COLOR,
    };
  });
}

function setKlineData(candles) {
  if (!candles || candles.length === 0) return;
  klineData = candles;
  if (showTimeshare) return;
  initChart();
  if (!candleSeries) return;
  var lc = _toLC(candles);
  candleSeries.setData(lc);
  volumeSeries.setData(_volumeData(candles));
  chart.timeScale().fitContent();
}

function setDayKlineData(candles) {
  if (!candles || candles.length === 0) return;
  dailyData = candles;
  if (showTimeshare) return;
  initChart();
  if (!candleSeries) return;
  var lc = _toLC(candles);
  candleSeries.setData(lc);
  volumeSeries.setData(_volumeData(candles));
  chart.timeScale().fitContent();
}

function drawKline() {
  var data = klineData;
  if (displayPeriod === 'kline-1d' || displayPeriod === 'kline-1w' || displayPeriod === 'kline-1m') {
    data = dailyData;
  }
  if (!data || data.length === 0) return;
  setKlineData(data);
}

function switchDisplayPeriod(period) {
  displayPeriod = period;
  if (period === 'kline-1d' || period === 'kline-1w' || period === 'kline-1m') {
    if (dailyData.length > 0) setKlineData(dailyData);
    return;
  }
  if (klineData.length > 0) setKlineData(klineData);
}

function setIndicator(name) {
  currentIndicator = name;
  // lightweight-charts doesn't have built-in indicators
  // We draw MA lines on top using addLineSeries
  drawIndicatorLines();
}

function drawIndicatorLines() {
  clearIndicatorLines();
  if (!candleSeries || klineData.length < 20) return;

  var data = klineData;
  var closePrices = data.map(function(c) { return c.close; });

  if (currentIndicator === 'MACD') {
    addLineSeries(calcMA(closePrices, 12), '#3b82f6', 'EMA12');
    addLineSeries(calcMA(closePrices, 26), '#f59e0b', 'EMA26');
  } else if (currentIndicator === 'BOLL') {
    var ma20 = calcMA(closePrices, 20);
    var std = calcStd(closePrices, 20);
    addLineSeries(ma20, '#8b5cf6', 'MA20');
    addLineSeries(ma20.map(function(v, i) {
      return v != null ? v + std[i] * 2 : null;
    }), '#8b5cf6', 'UP');
    addLineSeries(ma20.map(function(v, i) {
      return v != null ? v - std[i] * 2 : null;
    }), '#8b5cf6', 'DOWN');
  } else if (currentIndicator === 'RSI') {
    var rsi = calcRSI(closePrices, 14);
    addLineSeries(rsi, '#f59e0b', 'RSI');
  } else if (currentIndicator === 'KDJ') {
    var kdj = calcKDJ(data);
    addLineSeries(kdj.k, '#3b82f6', 'K');
    addLineSeries(kdj.d, '#f59e0b', 'D');
    addLineSeries(kdj.j, '#8b5cf6', 'J');
  }
}

function addLineSeries(data, color, label) {
  if (!chart || !data || data.length === 0) return;
  var lcTimes = klineData.map(function(c) { return Math.floor(c.time / 1000); });
  var seriesData = [];
  for (var i = 0; i < data.length; i++) {
    if (data[i] != null) {
      seriesData.push({ time: lcTimes[i], value: data[i] });
    }
  }
  if (seriesData.length === 0) return;
  var series = chart.addLineSeries({
    color: color,
    lineWidth: 1,
    priceLineVisible: false,
    lastValueVisible: false,
    title: label || '',
  });
  series.setData(seriesData);
  _indicatorLines.push(series);
}

function clearIndicatorLines() {
  if (chart) {
    _indicatorLines.forEach(function(s) {
      try { chart.removeSeries(s); } catch(e) {}
    });
  }
  _indicatorLines = [];
}

// ============================================================
// Timeshare (分时) — canvas rendering (unchanged)
// ============================================================
function setTimeshareData(data) {
  timeshareData = data || [];
  if (showTimeshare) drawTimeshare();
}

function toggleChartMode(mode) {
  if (mode === 'timeshare' || mode === 'chart') {
    showTimeshare = true;
    drawTimeshare();
  } else {
    showTimeshare = false;
    drawKline();
  }
}

function drawTimeshare() {
  var canvas = document.getElementById('kline-canvas');
  if (!canvas) return;
  var ctx = canvas.getContext('2d');
  var rect = canvas.parentElement.getBoundingClientRect();
  var W = canvas.width = rect.width - 0;
  var H = canvas.height = rect.height - 0;
  if (W <= 0 || H <= 0) return;

  var data = timeshareData || [];
  ctx.clearRect(0, 0, W, H);

  if (data.length < 2) {
    ctx.fillStyle = '#5a7a8a';
    ctx.font = '13px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('等待行情数据...', W / 2, H / 2);
    return;
  }

  var prices = data.map(function(d) { return d.price; });
  var minP = Math.min.apply(null, prices);
  var maxP = Math.max.apply(null, prices);
  var range = maxP - minP || 1;
  var pad = 10;
  var graphH = H - pad * 2;
  var graphW = W - pad * 2;

  // Grid lines
  ctx.strokeStyle = '#1a2c38';
  ctx.lineWidth = 1;
  for (var i = 0; i <= 4; i++) {
    var y = pad + (graphH / 4) * i;
    ctx.beginPath();
    ctx.moveTo(pad, y);
    ctx.lineTo(W - pad, y);
    ctx.stroke();
    var price = maxP - (range / 4) * i;
    ctx.fillStyle = '#5a7a8a';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(price.toFixed(2), pad - 4, y + 3);
  }

  // Price line
  var firstPrice = data[0].price;
  var lastClose = data[data.length - 1].price;
  var color = lastClose >= firstPrice ? KLINE.UP_COLOR : KLINE.DOWN_COLOR;

  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.beginPath();
  for (var i = 0; i < data.length; i++) {
    var x = pad + (i / (data.length - 1)) * graphW;
    var y = pad + (1 - (data[i].price - minP) / range) * graphH;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();

  // Fill below line
  ctx.lineTo(pad + graphW, pad + graphH);
  ctx.lineTo(pad, pad + graphH);
  ctx.closePath();
  var grad = ctx.createLinearGradient(0, pad, 0, pad + graphH);
  grad.addColorStop(0, color + '40');
  grad.addColorStop(1, color + '05');
  ctx.fillStyle = grad;
  ctx.fill();

  // Volume bars
  if (data[0].volume !== undefined) {
    var maxVol = 1;
    data.forEach(function(d) { if (d.volume > maxVol) maxVol = d.volume; });
    var volH = 30;
    ctx.fillStyle = color + '30';
    for (var i = 0; i < data.length; i++) {
      var x = pad + (i / (data.length - 1)) * graphW;
      var barW = Math.max(1, graphW / data.length - 1);
      var barH = (data[i].volume / maxVol) * volH;
      ctx.fillRect(x - barW / 2, pad + graphH - barH, barW, barH);
    }
  }

  // Time labels
  ctx.fillStyle = '#5a7a8a';
  ctx.font = '10px sans-serif';
  ctx.textAlign = 'center';
  var labelCount = Math.min(5, data.length);
  var step = Math.floor(data.length / (labelCount - 1));
  for (var i = 0; i < data.length; i += step) {
    var x = pad + (i / (data.length - 1)) * graphW;
    var t = data[i].time || '';
    if (typeof t === 'number') {
      var d = new Date(t);
      t = ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2);
    }
    ctx.fillText(t, x, H - 2);
  }
}

// ============================================================
// Indicator calculations (kept from previous kline.js)
// ============================================================
function calcMA(data, period) {
  var result = [];
  for (var i = 0; i < data.length; i++) {
    if (i < period - 1) { result.push(null); continue; }
    var sum = 0;
    for (var j = i - period + 1; j <= i; j++) sum += data[j];
    result.push(sum / period);
  }
  return result;
}

function calcStd(data, period) {
  var ma = calcMA(data, period);
  var result = [];
  for (var i = 0; i < data.length; i++) {
    if (i < period - 1) { result.push(null); continue; }
    var sum = 0;
    for (var j = i - period + 1; j <= i; j++) sum += Math.pow(data[j] - ma[i], 2);
    result.push(Math.sqrt(sum / period));
  }
  return result;
}

function calcRSI(data, period) {
  var result = [];
  if (data.length < period + 1) return result;
  result.push(null);
  var gains = 0, losses = 0;
  for (var i = 1; i <= period; i++) {
    var diff = data[i] - data[i-1];
    gains += Math.max(diff, 0);
    losses += Math.max(-diff, 0);
  }
  var avgGain = gains / period;
  var avgLoss = losses / period;
  result.push(avgLoss === 0 ? 100 : 100 - (100 / (1 + avgGain / avgLoss)));
  for (var i = period + 1; i < data.length; i++) {
    var diff = data[i] - data[i-1];
    avgGain = (avgGain * (period - 1) + Math.max(diff, 0)) / period;
    avgLoss = (avgLoss * (period - 1) + Math.max(-diff, 0)) / period;
    result.push(avgLoss === 0 ? 100 : 100 - (100 / (1 + avgGain / avgLoss)));
  }
  return result;
}

function calcKDJ(candles) {
  var result = { k: [], d: [], j: [] };
  if (candles.length < 9) return result;
  var rsv = [];
  for (var i = 0; i < candles.length; i++) {
    if (i < 8) { rsv.push(null); continue; }
    var h = -Infinity, l = Infinity;
    for (var j = i - 8; j <= i; j++) {
      if (candles[j].high > h) h = candles[j].high;
      if (candles[j].low < l) l = candles[j].low;
    }
    rsv.push(h === l ? 50 : ((candles[i].close - l) / (h - l)) * 100);
  }
  var prevK = 50, prevD = 50;
  for (var i = 0; i < candles.length; i++) {
    if (rsv[i] == null) {
      result.k.push(null); result.d.push(null); result.j.push(null);
      continue;
    }
    var k = (2 / 3) * prevK + (1 / 3) * rsv[i];
    var d = (2 / 3) * prevD + (1 / 3) * k;
    var j = 3 * k - 2 * d;
    result.k.push(k); result.d.push(d); result.j.push(j);
    prevK = k; prevD = d;
  }
  return result;
}
