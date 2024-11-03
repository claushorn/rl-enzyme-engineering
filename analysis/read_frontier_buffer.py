import os
import pandas as pd
import pickle
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.helpers import this_package_path

def read_frontier_buffer(sdate):
    sPath = this_package_path()+f'/rl-enzyme-engineering/experiments/{sdate}/'
    def load_data(): # all generation files that exist
        df = pd.DataFrame()
        files = os.listdir(sPath)
        files = [file for file in files if 'frontier_buffer_generation' in file]
        for file in files:
            i_generation = int(file.split('frontier_buffer_generation')[1].split('.pkl')[0])
            with open(sPath+file, 'rb') as f:
                sequences, scores, counts, other_scores = pickle.load(f)
            df = df.append(pd.DataFrame({'generation': i_generation, 'sequences': sequences, 'scores': scores, 'counts': counts, 'other_scores': other_scores}))
        return df
    return load_data()
