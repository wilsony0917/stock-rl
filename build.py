#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wilson stock-rl v2 builder

用途：
1. Python 每天下載/計算股票資料
2. 輸出 docs/data/stock.json
3. 複製 template/base.html、main.js、style.css、config.js 到 docs/
4. git push 更新 GitHub Pages
"""

import os
import json
import shutil
import subprocess
import datetime as dd

import numpy as np
import pandas as pd
import yfinance as yf
import requests
import logging
import warnings
from io import StringIO

logging.getLogger("yfinance").disabled = True
logging.getLogger("yfinance").propagate = False
logging.getLogger("yfinance").setLevel(0)
warnings.filterwarnings("ignore")

Now = lambda: format(dd.datetime.now(), "%Y-%m-%d %H:%M:%S")

Gr = [
    ["電子零組件業", "電腦及週邊設備業", "其他電子業", "電子通路業", "電器電纜", "電機機械", "光電業"],
    ["半導體業", "通信網路業", "資訊服務業", "數位雲端", "汽車工業", "航運業"],
    ["生技醫療業", "其他業", "鋼鐵工業", "化學工業", "綠能環保", "文化創意業"],
    ["建材營造業", "觀光餐旅", "金融保險業", "居家生活", "食品工業", "運動休閒", "貿易百貨業",
     "橡膠工業", "造紙工業", "水泥工業", "玻璃陶瓷", "農業科技業", "塑膠工業", "油電燃氣業", "紡織纖維"]
]


def catch_html(url):
    html = requests.get(url)
    html.encoding = "MS950"
    return pd.read_html(StringIO(html.text))


def fast_download_stocks():
    url = "https://isin.twse.com.tw/isin/class_main.jsp?owncode=&stockname=&isincode=&market="
    tail = "&industry_code=&Page=1&chklike=Y"
    urls = [
        url + "1&issuetype=1" + tail,
        url + "2&issuetype=4" + tail,
        url + "C&issuetype=" + tail,
    ]

    dfs = [catch_html(u)[0].T for u in urls]
    dfs = [d.set_index(d.columns[0]).T for d in dfs]
    df = pd.concat(dfs)

    df.rename(columns={
        "國際證券辨識號碼": "ISIN",
        "公開發行/上市(櫃)/發行日": "IPO",
        "有價證券名稱": "name",
        "市場別": "Market",
        "產業別": "Type",
        "有價證券代號": "Code",
    }, inplace=True)

    df = df.reindex(columns=["name", "Code", "IPO", "Market", "Type"])

    is_tpex = df["Market"].isin(["上櫃"])
    df["tv"] = np.where(is_tpex, "TPEX:", "TWSE:") + df["Code"].astype(str)
    df["yahoo"] = df["Code"].astype(str) + np.where(is_tpex, ".TWO", ".TW")

    df.set_index("Code", drop=False, inplace=True)
    df.sort_values("IPO", inplace=True)
    print("stocks list OK")
    return df


def download_by_stock(lc, interval="1d", period="2y", List=[]):
    if not isinstance(lc, pd.DataFrame):
        print("lc not dataframe")
        return {}

    if List != []:
        lc = lc.loc[List]

    print(Now(), "Start downloading")
    opts = {"interval": interval, "ignore_tz": True}
    data = {}
    total = len(lc.index)

    for n, code in enumerate(lc.index):
        try:
            df = yf.download(lc.loc[code, "yahoo"], **opts, progress=False, period=period)
            if isinstance(df.columns, pd.MultiIndex):
                df = df.droplevel(level=1, axis=1)
            data[str(code)] = df
        except Exception as e:
            print("\nDownload error", code, e)
            data[str(code)] = pd.DataFrame()

        print("\r", n + 1, "/", total, code, f"{lc.loc[code,'name']: <10}", end="", flush=True)

    print()
    return data


def D2WM(Dict, keys, dwm=None, df_txt=None):
    if dwm is None:
        dwm = {}
    if df_txt is None:
        df_txt = {}

    Times = ["D", "W", "ME"]
    zh_time = {"D": "日", "W": "週", "ME": "月"}

    for Time in Times:
        empty = [k for k, df in Dict.items() if len(df) < 1]
        if empty:
            print(Time, "empty df", empty[:20])

        clean = {k: df.copy() for k, df in Dict.items() if len(df) > 0}

        for k, df in clean.items():
            df.replace(0, np.nan, inplace=True)
            df.dropna(axis=0, how="any", inplace=True)
            df.sort_index(ascending=True, inplace=True)
            df.columns.set_names(str(keys[k]), inplace=True)
            df.index.set_names(str(keys[k]["name"]), inplace=True)

        print("\n", Now(), "resampling to", Time)
        col_name = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}

        if Time == "D":
            for k, df in clean.items():
                df["Volume"] = df["Volume"].div(1000).round(0)
            X = {k: df.copy() for k, df in clean.items()}
        else:
            X = {k: df.resample(Time).agg(col_name) for k, df in clean.items()}

        for k, df in X.items():
            df.dropna(axis=0, how="any", inplace=True)
            if len(df) == 0:
                continue

            Cbig = df["Close"] > df["Open"]
            Csml = df["Close"] < df["Open"]
            df["%"] = (df["Close"] / df["Close"].shift(1) - 1) * 100
            df["RB"] = Cbig.astype(int) - Csml.astype(int)
            df["RB"] = df["RB"].replace({-1: "l", 1: "u", 0: "."})

            txt = "".join(df["RB"].astype(str).values)
            tv_symbol = keys[k].get("tv", "")
            sub_name = zh_time[Time] + " " + tv_symbol + " " + df.index.name
            df_txt[sub_name] = txt

            if len(df) > 30:
                X[k] = df.iloc[-300:]

        dwm[Time] = X

    dwm["txt"] = df_txt
    return dwm


def find_repo():
    candidates = [
        os.path.expanduser("~/stock-rl"),
        os.path.expanduser("~/Desktop/stock-rl"),
    ]
    for p in candidates:
        if os.path.isdir(os.path.join(p, ".git")):
            return p
    raise FileNotFoundError("找不到 stock-rl git repo")


def push_to_github(repo_path):
    status = subprocess.run(["git", "status", "--porcelain"], cwd=repo_path, capture_output=True, text=True)
    if not status.stdout.strip():
        print("No changes")
        return

    msg = dd.datetime.now().strftime("Daily update %Y-%m-%d %H:%M")
    cmds = [
        ["git", "pull"],
        ["git", "add", "."],
        ["git", "commit", "-m", msg],
        ["git", "push"],
    ]

    for cmd in cmds:
        print("\n>", " ".join(cmd))
        result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)


def prepare_dirs(repo_path):
    for p in [
        os.path.join(repo_path, "template"),
        os.path.join(repo_path, "docs"),
        os.path.join(repo_path, "docs", "data"),
    ]:
        os.makedirs(p, exist_ok=True)


def publish_static_files(repo_path):
    mapping = {
        "base.html": "index.html",
        "main.js": "main.js",
        "style.css": "style.css",
        "config.js": "config.js",
    }
    for src, dst in mapping.items():
        src_path = os.path.join(repo_path, "template", src)
        dst_path = os.path.join(repo_path, "docs", dst)
        if os.path.exists(src_path):
            shutil.copy(src_path, dst_path)
        else:
            print("Missing template file:", src_path)


def write_stock_json(repo_path, TXT):
    out = {
        "updateTime": Now(),
        "stocks": TXT,
    }
    path = os.path.join(repo_path, "docs", "data", "stock.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("Saved:", path)


def upload_github(TXT):
    repo_path = find_repo()
    prepare_dirs(repo_path)
    publish_static_files(repo_path)
    write_stock_json(repo_path, TXT)
    push_to_github(repo_path)


def start_download():
    lc = fast_download_stocks()
    KEYS = {k: lc.loc[k].to_dict() for k in lc.index}
    df_stock = download_by_stock(lc)
    dwm = D2WM(df_stock, KEYS)
    return lc, df_stock, dwm


if __name__ == "__main__":
    lc, df_stock, dwm = start_download()
    upload_github(dwm["txt"])
