# stock-rl v2

## 結構

```text
stock-rl/
├── build.py
├── template/
│   ├── base.html
│   ├── main.js
│   ├── style.css
│   └── config.js
├── docs/
│   ├── index.html
│   ├── main.js
│   ├── style.css
│   ├── config.js
│   └── data/
│       └── stock.json
```

## 使用

1. 把 `template/` 和 `build.py` 放到你的 `stock-rl` repo 根目錄。
2. GitHub Pages 設成 `main / docs`。
3. 執行：

```bash
python build.py
```

程式會產生 `docs/data/stock.json`，複製 template 靜態檔案到 `docs/`，並自動 git push。
