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
  } catch (err) {
    status.textContent = "daily.json 讀取失敗：" + err.message;
    stockDataLoaded = false;
  }
}

function makeStockLink(row) {

    const safeKey = escapeHtml(row.key);
    const preview = escapeHtml(row.ul || "");

    const tvUrl =
        "https://tw.tradingview.com/chart/FKVV6Ftr/?symbol="
        + encodeURIComponent(row.tv);

    return `
        <div class="stock-link">

            <a class="stock-title"
               href="${tvUrl}"
               target="_blank">

                📈 ${safeKey}

            </a>

            <div class="preview">
                ${preview}
            </div>

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
    const keyword = document
        .getElementById("stockInput")
        .value
        .trim();

    const result = document.getElementById("result");

    if (!keyword) {
        result.innerHTML = "請輸入字串";
        return;
    }

    let pattern;

    try {
        pattern = new RegExp(keyword);
    } catch (e) {
        result.innerHTML = "Regex 格式錯誤：" + keyword;
        return;
    }

    const matched = stockRows.filter(row => {
        const text = [
            row.key || "",
            row.tv || "",
            row.symbol || "",
            row.ul || "",
            row.signal || ""
        ].join(" ");

        return pattern.test(text);
    });

    if (matched.length === 0) {
        result.innerHTML = "找不到：" + keyword;
        logSearch(keyword, 0);
        return;
    }

    result.innerHTML = matched
        .map(row => makeStockLink(row))
        .join("");

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
