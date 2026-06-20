#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 20 15:34:06 2025

@author: WilsonLiu
"""

import numpy as np
import pandas as pd
import yfinance as yf
import datetime,os
import requests,logging,warnings
from io import StringIO
import subprocess
import datetime as dd
import json
import re,time,shutil

logging.getLogger('yfinance').disabled = True
logging.getLogger('yfinance').propagate = False
logging.getLogger("yfinance").setLevel(0)
warnings.filterwarnings('ignore')
Now=lambda:format(dd.datetime.now(),'%Y-%m-%d %H:%M:%S')
Gr=[['電子零組件業','電腦及週邊設備業','其他電子業','電子通路業','電器電纜','電機機械','光電業'],
    ['半導體業', '通信網路業', '資訊服務業', '數位雲端','汽車工業','航運業'],
    ['生技醫療業', '其他業', '鋼鐵工業', '化學工業', '綠能環保', '文化創意業'],
    ['建材營造業','觀光餐旅','金融保險業','居家生活','食品工業','運動休閒','貿易百貨業',
     '橡膠工業','造紙工業','水泥工業','玻璃陶瓷','農業科技業','塑膠工業','油電燃氣業','紡織纖維']]

Name=os.environ['USER']
global Location_Dir
Location_Dir={'wilsonliu':'~/stock-rl','90001108':'~/Desktop/stock-rl'}[Name]

def catch_html(url):
    html=requests.get(url)
    html.encoding = "MS950"
    dfx = pd.read_html(StringIO(html.text))
    return dfx
    
def fast_download_stocks():
    df=pd.DataFrame()
    url='https://isin.twse.com.tw/isin/class_main.jsp?owncode=&stockname=&isincode=&market='
    tail='&industry_code=&Page=1&chklike=Y'
    hs=[url + '1&issuetype=1' + tail, url + '2&issuetype=4' + tail, url + 'C&issuetype=' + tail]
    df=[catch_html(u)[0].T for u in hs]
    df=[d.set_index(d.columns[0]).T for d in df]
    df=pd.concat(df)
    df.rename(columns={'國際證券辨識號碼':'ISIN', '公開發行/上市(櫃)/發行日':'IPO','有價證券名稱':'name',
                       '市場別':'Market', '產業別':'Type','有價證券代號':'Code'},inplace=True)
    df=df.reindex(columns=['name','Code','IPO','Market','Type'])
    
    df['yahoo']=df['Market'].isin(['上櫃'])
    df['tv']=df['yahoo'].replace(True,'TPEX:')
    df['tv']=df['tv'].replace(False,'TWSE:')
    df['tv']=df['tv'] + df['Code'].astype(str)
    df.replace(True,'.TWO',inplace=True)
    df.replace(False,'.TW',inplace=True)
    df['yahoo']=df['Code'] + df['yahoo']
    df.set_index('Code',drop=False,inplace=True)
    df.sort_values('IPO',inplace=True)
    print('stocks list OK')
    return df

def download_by_stock(lc,interval='1d',period='3y',List=[],D={}):
    if type(lc)!=pd.DataFrame:return print('lcc not dataframe')
    if List!=[]:lc=lc.loc[List]
    print(Now(),'Start download')
    index={'interval':interval,'ignore_tz':True}
    C=lambda l,x:l.loc[x,'Code']
    L=len(lc.index)
    for x,i in enumerate(lc.index):
        D[C(lc,i)]=yf.download(lc.loc[i,'yahoo'],**index,progress=False,period=period).droplevel(level=1,axis=1)
        print('\r','[',x+1,'/',L,']',i,f"{lc.loc[i,'name']: <10}",end="", flush=True)
    print('\n',Now(),'Stop download')
    return D

def D2WM(Dict0,lc,dwm={},df_txt={},df_tv={}):
    keys={k:lc.loc[k].to_dict() for k in lc.index}
    Times=['D','W','ME']
    zh_time={'D':'日','W':'週','ME':'月'}
    for Time in Times:
        len0=[k for k,df in Dict0.items() if len(df)<1]
        if len(len0)>0:print(Time,'empty df',len0)
        Dict={k:df.copy() for k,df in Dict0.items() if len(df)>0}
        [df.replace(0,np.nan,inplace=True) for k,df in Dict.items()]
        [df.dropna(axis=0,how='any',inplace=True) for k,df in Dict.items()]
        [df.sort_index(ascending=True,inplace=True) for k,df in Dict.items()]
        [df.columns.set_names(str(keys[k]),inplace=True) for k,df in Dict.items()]
        [df.index.set_names(str(keys[k]['name']),inplace=True) for k,df in Dict.items()]
        print('\n',Now(),'resampling to',Time)
        ''' min - minute, H - hour, D - day, W - week, ME- month '''
        col_name={'Open': 'first','High': 'max','Low': 'min','Close': 'last','Volume': 'sum'}
        if Time=='D':
            for k,df in Dict.items():df['Volume'] = df['Volume'].div(1000).round(0)
            X={k:df.copy() for k,df in Dict.items()}
        else:X={k:df.resample(Time).agg(col_name) for k,df in Dict.items()}
        [df.dropna(axis=0,how='any',inplace=True) for k,df in X.items()]
        for k,df in X.items():
            Cbig=df['Close'] > df['Open']
            Csml=df['Close'] < df['Open']
            df['%']= (df['Close']/df['Close'].shift(1)-1)*100
            df['RB'] = Cbig.astype(int) - Csml.astype(int)
            df['RB']=df['RB'].replace(-1,'l')
            df['RB']=df['RB'].replace(1,'u')
            df['RB']=df['RB'].replace(0,'.')
            df=df.round(2)
            txt=''.join(df['RB'].values)
            sub_name = zh_time[Time] + ' ' + str(k) + ' ' + df.index.name
            df_txt[sub_name]=txt[-60:]
            df_tv[sub_name]=keys[k]['tv']
    df=pd.DataFrame([df_txt,df_tv],index=['ul','tv']).T
    return df

def start_download():
    lc=fast_download_stocks()
    df_stock=download_by_stock(lc)
    dwm=D2WM(df_stock,lc)
    return lc,df_stock,dwm

def find_stock(df,S=''):
    if S=='':return
    i=df[df['ul'].str.contains(S)].index
    [print(a) for a in i]
    return i

def get_repo_path():
    """依使用者帳號判斷 stock-rl repo 位置。"""
    user = os.environ.get("USER", "")

    if user == "wilsonliu":return os.path.expanduser("~/stock-rl")
    return os.path.expanduser("~/Desktop/stock-rl")


def deploy_static_files():
    """
    把 template/ 的前端檔案複製到 docs/。
    Location_Dir = repo 根目錄，例如 ~/stock-rl
    """
    Location_Dir = get_repo_path()
    template_dir = os.path.join(Location_Dir, "template")
    docs_dir = os.path.join(Location_Dir, "docs")
    data_dir = os.path.join(docs_dir, "data")

    os.makedirs(docs_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    pairs = [("base.html", "index.html"),("main.js", "main.js"),
             ("style.css", "style.css"),("config.js", "config.js"),]

    for src_name, dst_name in pairs:
        src = os.path.join(template_dir, src_name)
        dst = os.path.join(docs_dir, dst_name)
        if os.path.exists(src):
            shutil.copy(src, dst)
        else:
            print("Missing template file:", src)


def normalize_json_records(json_data):
    """
    將 DataFrame / dict 轉成 daily.json 裡的 data list。

    支援格式：
    1. DataFrame 有 key/symbol/signal 欄位
    2. DataFrame 有 tv/signal 欄位
    3. DataFrame index 是 key，第一欄是 signal
    4. dict: {key: signal}
    """
    records = []

    if isinstance(json_data, pd.DataFrame):
        df = json_data.copy()

        # 欄名統一小寫方便判斷
        colmap = {str(c).lower(): c for c in df.columns}

        key_col = colmap.get("key") or colmap.get("name") or colmap.get("stock")
        symbol_col = colmap.get("symbol") or colmap.get("tv")
        signal_col = (colmap.get("signal") or colmap.get("ul") or colmap.get("rb") or colmap.get("value"))

        if signal_col is None and len(df.columns) > 0:signal_col = df.columns[0]

        for idx, row in df.iterrows():
            signal = "" if signal_col is None else str(row.get(signal_col, ""))
            symbol = "" if symbol_col is None else str(row.get(symbol_col, ""))

            if key_col is not None:key = str(row.get(key_col, idx))
            else:key = str(idx)

            # 若 key 裡沒有 TWSE/TPEX，但 symbol 有，就補進 key 前面，方便前端抓股號
            if symbol and symbol not in key:key = f"{key} {symbol}"

            records.append({"key": key,"symbol": symbol,"signal": signal,})

    elif isinstance(json_data, dict):
        for key, signal in json_data.items():
            key = str(key)
            symbol = ""
            # 從 key 裡抓 TWSE:2330 / TPEX:6125
            for part in key.split():
                if part.startswith("TWSE:") or part.startswith("TPEX:"):
                    symbol = part
                    break

            records.append({"key": key,"symbol": symbol,"signal": str(signal),})

    else:raise TypeError("json_data 必須是 pandas DataFrame 或 dict")

    return records


def update_json(json_data, update_time, Json_Name):
    """
    產生 daily.json。

    json_data: DataFrame 或 dict
    update_time: 每日更新時間字串，例如 Now()
    Json_Name: daily.json 完整路徑，例如 ~/stock-rl/docs/data/daily.json
    """
    records = normalize_json_records(json_data)
    payload = {"updateTime": update_time,"data": records,}
    
    Json_Name = os.path.expanduser(Json_Name)
    os.makedirs(os.path.dirname(Json_Name), exist_ok=True)

    with open(Json_Name, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print("JSON saved:", Json_Name)
    print("Records:", len(records))

    return Json_Name


def push_to_github(repo_path):
    """提交並推送 GitHub。沒有變更時不 commit。"""
    repo_path = os.path.expanduser(repo_path)

    # 先同步遠端，降低兩台電腦衝突機率
    pull = subprocess.run(["git", "pull"],cwd=repo_path,capture_output=True,text=True)
    if pull.stdout:print(pull.stdout)
    if pull.stderr:print(pull.stderr)

    status = subprocess.run(["git", "status", "--porcelain"],cwd=repo_path,capture_output=True,text=True)

    if not status.stdout.strip():return print("No changes")

    msg = dd.datetime.now().strftime("Daily update %Y-%m-%d %H:%M")

    cmds = [["git", "add", "."],["git", "commit", "-m", msg],["git", "push"],]

    for cmd in cmds:
        result = subprocess.run(cmd,cwd=repo_path,capture_output=True,text=True)
        print(">", " ".join(cmd))
        if result.stdout:print(result.stdout)
        if result.stderr:print(result.stderr)

def upload_github(json_data, update_time=None):
    """
    上傳每日資料。
    現在不再產生 index.html，只更新 docs/data/daily.json。
    """
    if update_time is None:update_time = Now()

    Location_Dir = get_repo_path()
    Json_Name = os.path.join(Location_Dir, "docs", "data", "daily.json")

    # 第一次升級 v2 時需要；之後留著也沒壞處
    deploy_static_files()

    update_json(json_data=json_data,update_time=update_time,Json_Name=Json_Name)

    push_to_github(Location_Dir)

    return Json_Name



dfs,lc,df_stock,dwm=start_download()
upload_github(dwm['txt'])


