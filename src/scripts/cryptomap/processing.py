import os
import sys

import pandas as pd

# Sets the current directory
os.chdir(sys.path[0])



if __name__ == '__main__':

    # Reads the csv
    df = pd.read_csv("./../../datasets/raw/cryptomap.csv")

    # Keeps only useful columns
    df = df[['id', 'symbol', 'base_asset', 'name', 'slug']]