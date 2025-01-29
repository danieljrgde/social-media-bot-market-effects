import glob
import multiprocessing as mp
import os
import pathlib
import sys
import time
from datetime import datetime

import pandas as pd
from IPython.display import display
from requests import Session

# Sets the current directory
os.chdir(sys.path[0])



#------------------------------#
#--- AUXILIARY FUNCTIONS ------#
#------------------------------#

def print_summary(df_summary, base_assets, start):    

    # Global summary
    df_global_summary = pd.DataFrame([{
        'n_twits': df_summary['n_twits'].sum(),
        'enlapsed_time': str(datetime.now()-start),
        'n_finished': df_summary[df_summary['status'] == 'done'].shape[0],
        'n_skipped': df_summary[df_summary['status'] == 'skipped'].shape[0],
        'n_errors': df_summary[df_summary['status'] == 'error'].shape[0],
        'n_remaning': len(base_assets) - df_summary[(df_summary['status'] == 'done') | (df_summary['status'] == 'skipped') | (df_summary['status'] == 'error')].shape[0]
    }])

    # Display the progress
    _ = os.system('cls')
    display(
        "STOCKTWITS INGESTION",
        "\n\n", 
        df_global_summary,
        "\n\n",
        df_summary[df_summary['status'] != 'skipped'].sort_values(['status', 'base_asset'], ascending=False).head(mp.cpu_count()+10)
    )



def get_twits(base_asset, status, safe_interrupt):

    if safe_interrupt.is_set():
        status.put({ 'base_asset': base_asset, 'n_twits': 0, 'status': 'skipped', 'iterations': 0 })
        return None

    # Starts a session
    s = Session()

    # Sets the HTTP request params
    url = f"https://api.stocktwits.com/api/2/streams/symbol/{base_asset}.X.json"
    headers = {}
    params = {
        'filter': 'top'
    }

    try:
        df_twits = pd.read_csv(f"./../../datasets/raw/tmp/stocktwits/{base_asset}.csv.gz", index_col=0, low_memory=False)
        params['max'] = df_twits.iloc[-1]['id']
    except:
        df_twits = pd.DataFrame()
    
    try:

        i, r = 0, { 'messages': True }
        while r['messages']:

            # Sends the HTTP request
            r = s.get(url, headers=headers, params=params)
            r = r.json()

            # Extracts twits
            df_tmp = pd.DataFrame(r['messages'])
            df_twits = pd.concat([df_twits, df_tmp], ignore_index=True)

            # Updates the HTTP request params
            params['max'] = r['cursor']['max']

            # Updates status
            i += 1
            status.put({ 'base_asset': base_asset, 'n_twits': df_twits.shape[0], 'status': "running", 'iterations': i, 'min_date': df_twits['created_at'].min() })
        
    except KeyboardInterrupt:

        # Updates status
        status.put({ 'base_asset': base_asset, 'n_twits': df_twits.shape[0], 'status': "saving", 'iterations': i, 'min_date': df_twits['created_at'].min() })
        
        # Saves the collected twits
        pathlib.Path("./../../datasets/raw/tmp/stocktwits").mkdir(parents=True, exist_ok=True)
        df_twits.to_csv(f"./../../datasets/raw/tmp/stocktwits/{base_asset}.csv.gz")

        # Updates status
        status.put({ 'base_asset': base_asset, 'n_twits': df_twits.shape[0], 'status': "saved", 'iterations': i, 'min_date': df_twits['created_at'].min() })

        return None

    except:

        # Saves the collected twits
        if df_twits.shape[0] > 0:
            pathlib.Path("./../../datasets/raw/tmp/stocktwits").mkdir(parents=True, exist_ok=True)
            df_twits.to_csv(f"./../../datasets/raw/tmp/stocktwits/{base_asset}.csv.gz")

        status.put({ 'base_asset': base_asset, 'n_twits': df_twits.shape[0], 'status': "error", 'iterations': i, 'min_date': df_twits['created_at'].min() })
        return None

    # Saves the collected twits
    pathlib.Path("./../../datasets/raw/tmp/stocktwits").mkdir(parents=True, exist_ok=True)
    df_twits.to_csv(f"./../../datasets/raw/tmp/stocktwits/{base_asset}.csv")

    # Updates status
    status.put({ 'base_asset': base_asset, 'n_twits': df_twits.shape[0], 'status': "done", 'iterations': i, 'min_date': df_twits['created_at'].min() })

    return None



#------------------------------#
#--- MAIN ---------------------#
#------------------------------#

if __name__ == '__main__':

    # Obtains the base assets
    df_cryptomap = pd.read_csv("./../../datasets/raw/cryptomap.csv.gz", index_col=0)
    base_assets = df_cryptomap['base_asset'].tolist()

    # Initializes the progress indicator variables
    df_summary = pd.DataFrame(columns=['base_asset', 'n_twits', 'status', 'iterations', 'min_date'])
    safe_interrupt = mp.Manager().Event()
    status = mp.Manager().Queue()
    start = datetime.now()

    # Starts the pool to multiprocess the collection
    pool = mp.Pool(processes=mp.cpu_count(), maxtasksperchild=1)
    dfs_twits = pool.starmap_async(get_twits, [(base_asset, status, safe_interrupt) for base_asset in base_assets])

    try:
        while not dfs_twits.ready():
            time.sleep(0.01)
            while not status.empty():
                df_tmp = pd.DataFrame([status.get()])
                df_summary = pd.concat([df_tmp, df_summary], ignore_index=True)
                df_summary = df_summary.sort_values(['status', 'n_twits'], ascending=[False, True]).drop_duplicates('base_asset', keep='last', ignore_index=True)
                print_summary(df_summary, base_assets, start)
            
    except KeyboardInterrupt:
        safe_interrupt.set()
        while not dfs_twits.ready():
            time.sleep(0.01)
            while not status.empty():
                df_tmp = pd.DataFrame([status.get()])
                df_summary = pd.concat([df_tmp, df_summary], ignore_index=True)
                df_summary = df_summary.sort_values(['status', 'n_twits'], ascending=[False, True]).drop_duplicates('base_asset', keep='last', ignore_index=True)
                print_summary(df_summary, base_assets, start)                

    # Terminates the pool
    pool.terminate()
    
    # Concatenates all temporary files and saves the result
    df_twits, tmp_filenames = pd.DataFrame(), glob.glob("./../../datasets/raw/tmp/stocktwits/*.csv.gz")
    for tmp_filename in tmp_filenames:
        df_tmp = pd.read_csv(tmp_filename, index_col=0, low_memory=False)
        df_tmp['base_asset'] = pathlib.Path(tmp_filename).stem
        df_twits = pd.concat([df_twits, df_tmp], ignore_index=True)
    df_twits.to_csv("./../../datasets/raw/twits.csv.gz")