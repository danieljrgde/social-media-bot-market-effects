import ast
import os
import pathlib
import re
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
    df = pd.read_csv("./../../datasets/raw/twits.csv.gz", index_col=0)

    # Performs basic operations
    df = df[(df['date'] >= START_DATE) & (df['date'] < END_DATE)]
    df.drop_duplicates(ignore_index=True, inplace=True)

    # Expands likes
    df = df.join(pd.json_normalize(df['likes'].map(lambda x: ast.literal_eval(x) if not pd.isna(x) else {}).tolist()).add_prefix("likes."))

    # Expands reshares
    df = df.join(pd.json_normalize(df['reshares'].map(lambda x: ast.literal_eval(x) if not pd.isna(x) else {}).tolist()).add_prefix("reshares."))

    # Expands label
    df = df.join(pd.json_normalize(df['entities'].map(lambda x: ast.literal_eval(x) if not pd.isna(x) else {}).tolist()).add_prefix("entities."))

    # Extracts user id
    df['user.id'] = df['user'].apply(lambda x: re.search(r"{'id': (\d+),", x).group(1))

    # Creates a separete dataframe for users
    df_users = df[['user']]
    df_users = df_users.drop_duplicates().reset_index(drop=True)
    df_users = df_users.join(pd.json_normalize(df_users['user'].map(lambda x: ast.literal_eval(x) if not pd.isna(x) else {}).tolist()))
    df_users['user.n_twits'] = df_users.groupby('user.id')['user.id'].transform('size')
    df_users = df_users.drop_duplicates('id').reset_index(drop=True)
    df_users = df_users.drop('user', axis=1)

    # Renames and filters columns
    df.rename(columns={
        'body': 'text',
        'created_at': 'date',
        'likes.total': 'n_likes',
        'reshares.reshared_count': 'n_reshares',
        'entities.sentiment.basic': 'label'
    }, inplace=True)
    df = df[['id', 'date', 'base_asset', 'user_id', 'text', 'n_likes', 'n_reshares', 'label']]

    # Saves the twits dataframe
    pathlib.Path("./../../datasets/processed").mkdir(parents=True, exist_ok=True)
    df.to_csv("./../../datasets/processed/twits.csv.gz")

    # Saves the users dataframe
    pathlib.Path("./../../datasets/processed").mkdir(parents=True, exist_ok=True)
    df_users.to_csv("./../../datasets/processed/users.csv.gz")
