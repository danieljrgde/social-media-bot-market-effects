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

    # Loads the datasets
    df = pd.read_csv("./../../datasets/enhanced/twits.csv.gz", index_col=0, parse_dates=['date'], low_memory=False, nrows=1000000)#, skiprows=range(1, 20+1))

    # Loads the classifier model
    model = tf.keras.models.load_model("./../../models/bert")

    # Makes predictions for all samples
    df['label_pred_score'] = pd.Series(model.predict(df['text'].tolist(), use_multiprocessing=True).flatten(), index=df.index)
    df['label_pred'] = df['label_pred_score'].round()
    # df = df[['id', 'label_pred_score', 'label_pred']]

    #
    df_twits = pd.read_csv("./../../datasets/classified/twits.csv.gz", index_col=0, parse_dates=['date'], low_memory=False)
    if not 'label_pred_score' in df_twits.columns:
        df_twits['label_pred_score'] = pd.NA
    if not 'label_pred' in df_twits.columns:
        df_twits['label_pred'] = pd.NA
    df_twits = pd.merge(df_twits, df, how='left', left_index=True, right_index=True, suffixes=('', '_DROP'))
    df_twits['label_pred_score'] = df_twits['label_pred_score'].combine_first(df_twits['label_pred_score_DROP'])
    df_twits['label_pred'] = df_twits['label_pred'].combine_first(df_twits['label_pred_DROP'])
    df_twits = df_twits.filter(regex='^(?!.*_DROP)')

    # Saves the twits dataframe
    pathlib.Path("./../../datasets/classified").mkdir(parents=True, exist_ok=True)
    df_twits.to_csv("./../../datasets/classified/twits.csv.gz")