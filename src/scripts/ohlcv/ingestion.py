import glob
import multiprocessing as mp
import os
import pathlib
import sys
import time
from datetime import datetime

import pandas as pd
import requests
from IPython.display import display

# Sets the current directory
os.chdir(sys.path[0])



#------------------------------#
#--- AUXILIARY FUNCTIONS ------#
#------------------------------#

def print_summary(df_summary, base_assets, start):    

    # Global summary
    df_global_summary = pd.DataFrame([{
        'n_rows': df_summary['n_rows'].sum(),
        'enlapsed_time': str(datetime.now()-start),
        'n_finished': df_summary[df_summary['status'] == 'done'].shape[0],
        'n_skipped': df_summary[df_summary['status'] == 'skipped'].shape[0],
        'n_errors': df_summary[df_summary['status'] == 'error'].shape[0],
        'n_remaning': len(base_assets) - df_summary[df_summary['status'] == 'done'].shape[0]
    }])

    # Display the progress
    _ = os.system('cls')
    display(
        "OHLCV INGESTION",
        "\n\n", 
        df_global_summary,
        "\n\n",
        df_summary[df_summary['status'] != 'skipped'].sort_values(['status', 'base_asset'], ascending=False).head(mp.cpu_count()+10)
    )



def get_ohlcv(base_asset, start_date, end_date, status, safe_interrupt):

    if safe_interrupt.is_set():
        status.put({ 'base_asset': base_asset, 'n_rows': 0, 'status': 'skipped', 'iterations': 0 })
        return None

    # Sets the HTTP request params
    url = "https://api.binance.com/api/v3/klines"
    params = {
        'symbol': f"{base_asset}USDT",
        'interval': '1h',
        'limit': 1000
    }

    try:
        df = pd.read_csv(f"./../../datasets/raw/tmp/ohlcv/{base_asset}.csv", index_col=0, parse_dates=['date'])
        params['startTime'] = int(df['date'].max().timestamp()*1E3)
    except Exception as e:
        df = pd.DataFrame()
        params['startTime'] = int(start_date.timestamp()*1E3)


    try:
        while params['startTime'] < int(end_date.timestamp()*1E3):

            # Makes the request
            r = requests.get(url, params=params)
            r = r.json()

            df_tmp = pd.DataFrame(r, columns=['date', '', '', '', 'price', 'vol', '', '', 'n_trades', '', '', ''])

            # Converts dtypes
            df_tmp = df_tmp.apply(pd.to_numeric, errors='ignore')
            df_tmp['date'] = pd.to_datetime(df_tmp['date'], unit='ms', utc=True).dt.tz_localize(None)

            # Selects important columns
            df_tmp = df_tmp[['date', 'price', 'vol', 'n_trades']]        

            # Appends the dataframe
            df = pd.concat([df, df_tmp], ignore_index=True)

            # Updates status
            status.put({ 'base_asset': base_asset, 'n_rows': df.shape[0], 'status': "running" })

            # Updates request params
            params['startTime'] = int(df['date'].max().timestamp() * 1E3 + 1)
        
    except KeyboardInterrupt:
        
        # Updates status
        status.put({ 'base_asset': base_asset, 'n_rows': df.shape[0], 'status': "saving" })
        
        # Saves the collected ohlcv
        pathlib.Path("./../../datasets/raw/tmp/ohlcv").mkdir(parents=True, exist_ok=True)
        df.to_csv(f"./../../datasets/raw/tmp/ohlcv/{base_asset}.csv")

        # Updates status
        status.put({ 'base_asset': base_asset, 'n_rows': df.shape[0], 'status': "saved" })

        return None

    except:
        status.put({ 'base_asset': base_asset, 'n_rows': df.shape[0], 'status': "error" })
        return None

    # Gets only ohlcv data from between start_date and end_date
    df = df[(start_date <= df['date']) & (df['date'] < end_date)]

    # Saves the collected twits
    pathlib.Path("./../../datasets/raw/tmp/ohlcv").mkdir(parents=True, exist_ok=True)
    df.to_csv(f"./../../datasets/raw/tmp/ohlcv/{base_asset}.csv")

    # Updates status
    status.put({ 'base_asset': base_asset, 'n_rows': df.shape[0], 'status': "done" })
    
    return None



#------------------------------#
#--- MAIN ---------------------#
#------------------------------#

if __name__ == '__main__':

    # Gets the arguments of the script
    _, START_DATE, END_DATE = tuple(sys.argv)
    START_DATE = datetime.fromisoformat(START_DATE)
    END_DATE = datetime.fromisoformat(END_DATE)

    # Obtains the base assets
    df_cryptomap = pd.read_csv("./../../datasets/raw/cryptomap.csv", index_col=0)
    base_assets = df_cryptomap['base_asset'].tolist()

    # Initializes the progress indicator variables
    df_summary = pd.DataFrame(columns=['base_asset', 'n_rows', 'status'])
    safe_interrupt = mp.Manager().Event()
    status = mp.Manager().Queue()
    start = datetime.now()

    # Starts the pool to multiprocess the collection
    pool = mp.Pool(processes=mp.cpu_count(), maxtasksperchild=1)
    dfs_ohlcv = pool.starmap_async(get_ohlcv, [(base_asset, START_DATE, END_DATE, status, safe_interrupt) for base_asset in base_assets])

    try:
        while not dfs_ohlcv.ready():
            time.sleep(0.01)
            while not status.empty():
                df_tmp = pd.DataFrame([status.get()])
                df_summary = pd.concat([df_tmp, df_summary], ignore_index=True)
                df_summary = df_summary.sort_values(['status', 'n_rows'], ascending=[False, True]).drop_duplicates('base_asset', keep='last', ignore_index=True)
                print_summary(df_summary, base_assets, start)
            
    except KeyboardInterrupt:
        safe_interrupt.set()
        while not dfs_ohlcv.ready():
            time.sleep(0.01)
            while not status.empty():
                df_tmp = pd.DataFrame([status.get()])
                df_summary = pd.concat([df_tmp, df_summary], ignore_index=True)
                df_summary = df_summary.sort_values(['status', 'n_rows'], ascending=[False, True]).drop_duplicates('base_asset', keep='last', ignore_index=True)
                print_summary(df_summary, base_assets, start) 

    # Terminates the pool
    pool.terminate()
    
    # Concatenates all temporary files and saves the result
    df_ohlcv, tmp_filenames = pd.DataFrame(), glob.glob("./../../datasets/raw/tmp/ohlcv/*.csv")
    for tmp_filename in tmp_filenames:
        df_tmp = pd.read_csv(tmp_filename, index_col=0)
        df_tmp['base_asset'] = pathlib.Path(tmp_filename).stem
        df_ohlcv = pd.concat([df_ohlcv, df_tmp], ignore_index=True)
    df_ohlcv.to_csv("./../../datasets/raw/ohlcv.csv")