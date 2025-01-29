import os
import pathlib
import sys

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()
os.chdir(sys.path[0])



#------------------------------#
#--- BINANCE TRADABLE ---------#
#------------------------------#

# Makes the HTTP request
r = requests.get("https://api.binance.com/api/v3/exchangeInfo")
r = r.json()

# Obtains tradable symbols
df1 = pd.DataFrame(r['symbols'])
df1 = df1[
    (df1['isSpotTradingAllowed'] == True) & \
    (df1['quoteAsset'] == 'USDT') & \
    (df1['status'] == 'TRADING')
]
symbols = df1['symbol'].unique()

# Deletes the dataframe from memory
del df1



#------------------------------#
#--- COINMARKETCAP RANKING ----#
#------------------------------#

url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
headers = {
    'Accepts': "application/json", 
    'X-CMC_PRO_API_KEY': os.environ.get("CMC_PRO_API_KEY")
}

# Makes the HTTP request
r = requests.get(url, headers=headers)
r = r.json()

# Builds the dataframe with tradable crypto information
df2 = pd.DataFrame(r['data'])

# Filters symbols tradable on Binance
df2['symbol'] = df2['symbol'].apply(lambda x: f"{x}USDT")
df2 = df2[df2['symbol'].isin(symbols)]
df2 = df2.sort_values('cmc_rank', ascending=True).drop_duplicates('symbol').reset_index(drop=True)

# Filters top 50 cryptos by market cap
df2 = df2.iloc[:50]

# Only keeps the ids of top 50 cryptos by marketcap
ids = df2['id'].astype(str).tolist()



#------------------------------#
#--- COINMARKETCAP INFO -------#
#------------------------------#

# Sets the HTTP request parameters
url = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/info"
headers = {
    'Accepts': "application/json", 
    'X-CMC_PRO_API_KEY': os.environ.get("CMC_PRO_API_KEY")
}
params = {
    'id': ','.join(ids)
}

# Makes the HTTP request
r = requests.get(url, headers=headers, params=params)
r = r.json()

# Builds the dataframe with tradable crypto information
df = pd.DataFrame([d for d in r['data'].values()])

# Corrects naming inconsistency
df['base_asset'] = df['symbol']
df['symbol'] = df['symbol'].apply(lambda x: f"{x}USDT")

# Saves the dataframe
pathlib.Path("./../../datasets/raw").mkdir(parents=True, exist_ok=True)
df.to_csv("./../../datasets/raw/cryptomap.csv")
