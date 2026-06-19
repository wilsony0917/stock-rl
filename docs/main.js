let stockData = {};

async function loadStockData() {
  try {
    const response = await fetch("data/stock.json?t=" + Date.now());
    const data = await response.json();

    stockData = data.stocks || {};
    document.getElementById("updateTime").textContent = data.updateTime || "Unknown";
    document.getElementById("result").textContent = "請輸入字串後查詢";

    openTV(CONFIG.defaultSymbol);
  } catch (e) {
    document.getElementById("result").textContent = "stock.json 讀取失敗";
    console.error(e);
  }
}

function getSymbol(key) {
  const parts = key.split(" ");
  return parts[1] || CONFIG.defaultSymbol;
}

function openTV(symbol) {
  const url = CONFIG.tradingViewUrl + encodeURIComponent(symbol);
  document.getElementById("tvFrame").src = url;
}

function makeStockLink(key) {
  const symbol = getSymbol(key);

  return `
    <div class="stock-link" onclick="openTV('${symbol}')">
      <div>${key}</div>
      <div class="stock-symbol">${symbol}</div>
    </div>
  `;
}

function logSearch(keyword, resultCount) {
  const logUrl =
    CONFIG.logUrl
    + "?keyword=" + encodeURIComponent(keyword)
    + "&resultCount=" + encodeURIComponent(resultCount)
    + "&userAgent=" + encodeURIComponent(navigator.userAgent)
    + "&t=" + Date.now();

  const img = new Image();
  img.src = logUrl;
}

function searchStock() {
  const keyword = document.getElementById("stockInput").value.trim();
  const result = document.getElementById("result");

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

  let output = "";
  let count = 0;

  for (const key in stockData) {
    if (pattern.test(stockData[key])) {
      output += makeStockLink(key);
      count += 1;
    }
  }

  if (count === 0) {
    result.innerHTML = "找不到：" + keyword;
  } else {
    result.innerHTML = `<div class="result">${output}</div>`;
  }

  logSearch(keyword, count);
}

document.getElementById("searchBtn").addEventListener("click", searchStock);

document.getElementById("stockInput").addEventListener("keydown", e => {
  if (e.key === "Enter") searchStock();
});

loadStockData();
