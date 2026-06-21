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

print("="*60)
print("Running :", __file__)
print("PWD     :", os.getcwd())
print("="*60)

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
global Location_Dir,download_path,stocks_save,trade_data

Location_Dir={'wilsonliu':'~/stock-rl','90001108':'~/Desktop/stock-rl'}[Name]
download_path = os.path.join(os.path.expanduser('~'), 'Downloads')
stocks_save = os.path.join(download_path,'stocks_save')
trade_data = os.path.join(download_path,'trade_data')

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

def download_by_stock(lc,interval='1d',period='',List=[],D={}):
    if type(lc)!=pd.DataFrame:return print('lcc not dataframe')
    if List!=[]:lc=lc.loc[List]
    print(Now(),'Start download')
    index={'interval':interval,'ignore_tz':True}
    C=lambda l,x:l.loc[x,'Code']
    L=len(lc.index)
    for x,i in enumerate(lc.index):
        D[C(lc,i)]=yf.download(lc.loc[i,'yahoo'],**index,progress=False,period=period).droplevel(level=1,axis=1)
        print('\r','[',x+1,'/',L,']',i,f"{lc.loc[i,'name']: <10}",end="", flush=True)
    print('\n',Now(),'finish download')
    return D

def D2WM(Dict0,lc,df_txt={},df_tv={}):
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
    
    df_no={k:v.split(':')[1] for k,v in df_tv.items()}
    df_yf={k:v.replace('TWSE:','TW.')for k,v in df_tv.items()}
    df_yf={k:v.replace('TPEX:','TWO.')for k,v in df_yf.items()}
    df=pd.DataFrame([df_txt,df_tv,df_no,df_yf],index=['ul','tv','num','yahoo']).T
    return df

def start_download():
    lc=fast_download_stocks()
    df_stock=download_by_stock(lc,interval='1d')
    new_dict=save_to_parquet(df_stock)
    dwm=D2WM(new_dict,lc)
    return lc,df_stock,dwm

def find_stock(df,S=''):
    if S=='':return
    i=df[df['ul'].str.contains(S)].index
    [print(a) for a in i]
    return i

def save_to_parquet(new_Dict):
    old_files = [os.path.join(stocks_save,b) for a in os.walk(stocks_save) for b in a[2]]
    old_dict={os.path.basename(f).split('.')[0]:pd.read_parquet(f) for f in old_files if f.endswith('parquet')}
    for k,df in new_Dict.items():
        new_file = os.path.join(stocks_save, k + '.parquet')
        if os.path.isfile(new_file)==True:old_dict[k]=pd.concat([old_dict[k],df],join='inner')
        else:old_dict[k]=df.copy()
        old_dict[k].to_parquet(new_file)
    return old_dict

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

def update_json(dwm, update_time, Json_Name):

    payload = {"updateTime": update_time,
               "data": dwm.reset_index().rename(columns={"index": "key"}).to_dict(orient="records")}

    Json_Name = os.path.expanduser(Json_Name)
    os.makedirs(os.path.dirname(Json_Name), exist_ok=True)

    with open(Json_Name, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print("JSON saved:", Json_Name)
    print("Records:", len(payload["data"]))
    return

def push_to_github(repo_path):
    """提交並推送 GitHub。沒有變更時不 commit。"""
    repo_path = os.path.expanduser(repo_path)
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
    if update_time is None:update_time = Now()
    Name = os.environ["USER"]
    if Name == "wilsonliu":repo_path = os.path.expanduser("~/stock-rl")
    else:repo_path = os.path.expanduser("~/Desktop/stock-rl")
    Json_Name = os.path.join(repo_path,"docs","data","daily.json")
    
    update_json(dwm=json_data,update_time=update_time,Json_Name=Json_Name)

    push_to_github(repo_path)
    return 

lc=fast_download_stocks()
df_stock=download_by_stock(lc,interval='1d')
new_dict=save_to_parquet(df_stock)
dwm=D2WM(new_dict,lc)

print("START upload_github")
upload_github(dwm)
print("END upload_github")

