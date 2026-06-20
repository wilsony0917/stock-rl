# stock-rl v2 daily.json 架構

## GitHub Pages 設定

Repository Settings → Pages：

- Source: Deploy from a branch
- Branch: main
- Folder: `/docs`

## 檔案結構

```text
stock-rl/
├── UHS_v1.py
├── UHS_v1_patch.py
├── template/
│   ├── base.html
│   ├── main.js
│   ├── style.css
│   └── config.js
└── docs/
    ├── index.html
    ├── main.js
    ├── style.css
    ├── config.js
    └── data/
        └── daily.json
```

## 每日更新

每天只需要更新：

```text
docs/data/daily.json
```

HTML / CSS / JS 不需要每天重新產生。

## UHS_v1.py 要做的事

把 `UHS_v1_patch.py` 裡的 function 貼到你的主程式，最後呼叫：

```python
lc, df_stock, dwm = start_download()
upload_github(你的_dataframe, Now())
```

`你的_dataframe` 建議包含：

- key：顯示名稱，例如 `日 TWSE:2330 台積電`
- symbol：TradingView 股號，例如 `TWSE:2330`
- signal：UL/RB 字串

若你的 DataFrame 只有 index + 第一欄 signal，程式也會嘗試自動轉換。

## Mac mini LaunchAgent

如果原本已經排程執行 Python，只需要把 `ProgramArguments` 裡的 script path 改成新的 `UHS_v1.py` 路徑。

修改後：

```bash
launchctl unload ~/Library/LaunchAgents/com.wilson.unhide_stock.plist
launchctl load ~/Library/LaunchAgents/com.wilson.unhide_stock.plist
launchctl print gui/$(id -u)/com.wilson.unhide_stock
```
