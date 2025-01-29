import math
import os
import pathlib
import sys

import pandas as pd
import tensorflow as tf
import tensorflow_hub as hub
import tensorflow_text as text



# Sets the current directory
os.chdir(sys.path[0])



if __name__ == "__main__":

    print("READING CSV")

    # Loads the datasets
    nrows = 1000000
    # df_twits = pd.read_csv("./../../datasets/enhanced/twits.csv.gz", index_col=0, parse_dates=['date'], low_memory=False, nrows=nrows, skiprows=None)
    # df_twits = pd.read_csv("./../../datasets/enhanced/twits.csv.gz", index_col=0, parse_dates=['date'], low_memory=False, nrows=nrows, skiprows=range(1, nrows+1))
    # df_twits = pd.read_csv("./../../datasets/enhanced/twits.csv.gz", index_col=0, parse_dates=['date'], low_memory=False, nrows=nrows, skiprows=range(1, 2*nrows+1))
    # df_twits = pd.read_csv("./../../datasets/enhanced/twits.csv.gz", index_col=0, parse_dates=['date'], low_memory=False, nrows=nrows, skiprows=range(1, 3*nrows+1))
    # df_twits = pd.read_csv("./../../datasets/enhanced/twits.csv.gz", index_col=0, parse_dates=['date'], low_memory=False, nrows=nrows, skiprows=range(1, 4*nrows+1))
    # df_twits = pd.read_csv("./../../datasets/enhanced/twits.csv.gz", index_col=0, parse_dates=['date'], low_memory=False, nrows=nrows, skiprows=range(1, 5*nrows+1))
    # df_twits = pd.read_csv("./../../datasets/enhanced/twits.csv.gz", index_col=0, parse_dates=['date'], low_memory=False, nrows=nrows, skiprows=range(1, 6*nrows+1))
    df_twits = pd.read_csv("./../../datasets/enhanced/twits.csv.gz", index_col=0, parse_dates=['date'], low_memory=False, nrows=nrows, skiprows=range(1, 7*nrows+1))

    # Loads the classifier model
    print("LOADING MODEL")
    model = tf.keras.models.load_model("./../../models/bert")

    # Makes predictions for all samples
    df_twits['label_pred_score'] = pd.Series(model.predict(df_twits['text'].tolist()).flatten(), index=df_twits.index)
    df_twits['label_pred'] = df_twits['label_pred_score'].round()

    # Saves the twits dataframe
    print("SAVING MODEL")
    pathlib.Path("./../../datasets/classified/tmp").mkdir(parents=True, exist_ok=True)
    df_twits.to_csv("./../../datasets/classified/tmp/twits_7.csv.gz")