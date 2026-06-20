let stockRows = [];
let stockDataLoaded = false;

function normalizeRows(payload) {
  if (Array.isArray(payload.data)) return payload.data;

  if (payload.stocks && typeof payload.stocks === "object") {
    return Object.entries(payload.stocks).map(([key, signal]) => ({
      key,
      signal,
      symbol: extractSymbolFromKey(key)
    }));
  }

  return [];
}

function extractSymbolFromKey(key) {
  const m = String(key).match(/(?:TWSE|TPEX):\d+/);
  return m ? m[0] : "";
}

async function loadDailyData() {
  const status = document.getElementById("status");

  try {
    const url = CONFIG.DATA_URL + "?t=" + Date.now();
    const response = await fetch(url);
    if (!response.ok) throw new Error("HTTP " + response.status);

    const payload = await response.json();
    stockRows = normalizeRows(payload).map(row => ({
    key: row.key || "",
    symbol: row.symbol || row.tv || extractSymbolFromKey(row.key || ""),
    signal: row.signal || row.ul || row.value || ""
    }));

    document.getElementById("updateTime").textContent = payload.updateTime || "未知";
    status.textContent = "已載入 " + stockRows.length + " 筆資料";
    stockDataLoaded = true;
    openTV(CONFIG.DEFAULT_SYMBOL);
  } catch (err) {
    status.textContent = "daily.json 讀取失敗：" + err.message;
    stockDataLoaded = false;
  }
}

function openTV(symbol) {
  if (!symbol) return;

  const url = CONFIG.TV_CHART_BASE + encodeURIComponent(symbol);
  document.getElementById("tvFrame").src = url;
}

function makeStockLink(row) {
  const safeKey = escapeHtml(row.key);
  const safeSymbol = escapeHtml(row.symbol || "");
  const preview = escapeHtml(String(row.signal || "").slice(-CONFIG.SIGNAL_PREVIEW_LEN));

  return `
    <div class="stock-link" onclick="openTV('${safeSymbol}')">
      <div><span class="stock-symbol">${safeKey}</span></div>
      <div class="stock-signal">${preview}</div>
    </div>
  `;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function searchStock() {
  const keyword = document.getElementById("stockInput").value.trim();
  const result = document.getElementById("result");

  if (!stockDataLoaded) {
    result.innerHTML = "資料尚未載入完成";
    return;
  }

  if (!keyword) {
    result.innerHTML = "請輸入字串";
    return;
  }

  let pattern;
  try {
    pattern = new RegExp(keyword);
  } catch (e) {
    result.innerHTML = "Regex 格式錯誤";
    return;
  }

  const matched = stockRows.filter(row => {
    const text = [
        row.key || "",
        row.symbol || "",
        row.signal || ""
    ].join(" ");

    return pattern.test(text);
  });

  if (matched.length === 0) {
    result.innerHTML = "找不到：" + escapeHtml(keyword);
  } else {
    result.innerHTML = "<div class='result'>" + matched.map(makeStockLink).join("") + "</div>";
    if (matched[0].symbol) openTV(matched[0].symbol);
  }

  logSearch(keyword, matched.length);
}

function logSearch(keyword, resultCount) {
  if (!CONFIG.LOG_URL) return;

  const logUrl =
    CONFIG.LOG_URL
    + "?keyword=" + encodeURIComponent(keyword)
    + "&resultCount=" + encodeURIComponent(resultCount)
    + "&userAgent=" + encodeURIComponent(navigator.userAgent)
    + "&t=" + Date.now();

  const img = new Image();
  img.src = logUrl;
}

function clearSearch() {
  document.getElementById("stockInput").value = "";
  document.getElementById("result").innerHTML = "請輸入字串後查詢";
}

document.getElementById("searchBtn").addEventListener("click", searchStock);
document.getElementById("clearBtn").addEventListener("click", clearSearch);
document.getElementById("stockInput").addEventListener("keydown", e => {
  if (e.key === "Enter") searchStock();
});

loadDailyData();
