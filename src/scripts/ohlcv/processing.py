import os
import pathlib
import sys
from datetime import datetime

import pandas as pd

# Sets the current directory
os.chdir(sys.path[0])



#------------------------------#
#--- MAIN ---------------------#
#------------------------------#

if __name__ == '__main__':

    # Gets the arguments of the script
    _, START_DATE, END_DATE = tuple(sys.argv)
    START_DATE = datetime.fromisoformat(START_DATE)
    END_DATE = datetime.fromisoformat(END_DATE)

    # Reads the dataset
    df = pd.read_csv("./../../datasets/raw/ohlcv.csv.gz", index_col=0, parse_dates=['date'], low_memory=False)
    df_cryptomap = pd.read_csv("./../../datasets/raw/cryptomap.csv.gz", index_col=0)

    # Performs basic operations
    df = df[(df['date'] >= START_DATE) & (df['date'] < END_DATE)]
    df = df[df['base_asset'].isin(df_cryptomap['base_asset'])]
    df.drop_duplicates(ignore_index=True, inplace=True)

    # Saves the ohlcv dataframe
    pathlib.Path("./../../datasets/processed").mkdir(parents=True, exist_ok=True)
    df.to_csv("./../../datasets/processed/ohlcv.csv.gz")