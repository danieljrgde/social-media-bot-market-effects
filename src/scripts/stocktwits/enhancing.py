import os
import pathlib
import re
import string
import sys
from datetime import datetime

import contractions
import emoji
import nltk
import pandas as pd
from wordcloud import STOPWORDS

# Sets the current directory
os.chdir(sys.path[0])

# Orders the stopwords
STOPWORDS = list(STOPWORDS)
STOPWORDS.sort(key=len, reverse=True)



#------------------------------#
#--- AUXILIARY FUNCTIONS ------#
#------------------------------#

def light_clean_text(text):
    """Preprocesses the text as described by the BERTweet paper. 
    Also implements generalization for stocktwits stock tags. 

    Args:
        text (str): text to be cleaned

    Returns:
        str: cleaned text
    """

    # Converts dtype
    text = str(text)

    # Puts the text in lower case
    text = text.lower()

    # Removes stocktwits base asset tags
    text = re.sub(r"\$([a-zA-Z]+)\.x", r"\1", text)

    # Replaces URLs by its special token (httpurl)
    text = re.sub(r"[A-Za-z0-9]+://[A-Za-z0-9%-_]+(/[A-Za-z0-9%-_])*(#|\\?)[A-Za-z0-9%-_&=]*", " httpurl ", text)

    # Applies tweet tokenizer
    tk = nltk.TweetTokenizer()
    text = tk.tokenize(text)

    # Merges the result
    text = " ".join(text)

    # Replaces user mentions by its special token (@user)
    text = re.sub(r"@[^\s]+", " @user ", text )

    # Translate emotion icons into text strings
    text = emoji.demojize(text)

    return text



def heavy_clean_text(text):
    """Uses more advanced text-cleaning methods.

    Args:
        text (str): light cleaned text

    Returns:
        str: heavy cleaned text
    """

    # Converts dtype
    text = str(text)

    # Replace 3 or more consecutive letters by 2 letter
    text = re.sub(r"(.)\1\1+", r"\1\1", text)

    # Removes repeated words in a row
    text = re.sub(r"\b(\w+)( \1\b)+", r"\1", text)

    # Removes numbers
    text = text.translate(str.maketrans("", "", string.digits))

    # Fix contractions
    text = contractions.fix(text)

    # Removes stopwords
    text = re.compile(r'\b%s\b' % r'\b|\b'.join(map(re.escape, STOPWORDS))).sub('', text)

    # Removes punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))

    # Applies tweet tokenizer
    tk = nltk.TweetTokenizer()
    text = tk.tokenize(text)

    # Merges the result
    text = " ".join(text)

    return text



#------------------------------#
#--- MAIN ---------------------#
#------------------------------#

if __name__ == "__main__":

    # Gets the arguments of the script
    _, START_DATE, END_DATE = tuple(sys.argv)
    START_DATE = datetime.fromisoformat(START_DATE)
    END_DATE = datetime.fromisoformat(END_DATE)

    # Loads the datasets
    df_twits = pd.read_csv("./../../datasets/processed/twits.csv.gz", index_col=0, parse_dates=['date'])
    df_users = pd.read_csv("./../../datasets/processed/users.csv.gz", index_col=0, parse_dates=['join_date'])

    # Adds information to the user dataframe
    df_users['n_active_days'] = df_users['join_date'].apply(lambda x: ( END_DATE - x ).days )
    df_users['n_active_days_clipped'] = df_users['join_date'].apply(lambda x: ( END_DATE - max(START_DATE, x) ).days )
    df_users['twit_freq'] = df_users['n_twits']/df_users['n_active_days_clipped']
    df_users['idea_freq'] = df_users['n_twits']/df_users['n_active_days']
    df_users['is_bot'] = ( df_users['twit_freq'] > df_users['twit_freq'].quantile(0.9) ) | \
                         ( df_users['idea_freq'] > df_users['idea_freq'].quantile(0.9) ) | \
                         ( df_users['following'] > df_users['following'].quantile(0.9) ) | \
                         ( df_users['like_count'] > df_users['like_count'].quantile(0.9) )

    # Adds information to the twits dataframe
    df_twits['user.type'] = df_twits['user.id'].isin(df_users[df_users['is_bot'] == True]['id']).replace({True: 'Bot', False: 'User'})
    df_twits['text_light_clean'] = df_twits['text'].apply(light_clean_text)
    df_twits['text_heavy_clean'] = df_twits['text_light_clean'].apply(heavy_clean_text)

    # Saves the users dataframe
    pathlib.Path("./../../datasets/enhanced").mkdir(parents=True, exist_ok=True)
    df_users.to_csv("./../../datasets/enhanced/users.csv.gz")

    # Saves the twits dataframe
    pathlib.Path("./../../datasets/enhanced").mkdir(parents=True, exist_ok=True)
    df_twits.to_csv("./../../datasets/enhanced/twits.csv.gz")