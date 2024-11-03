from read_frontier_buffer import read_frontier_buffer
import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator
#from src.helpers import this_package_path
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
import glob
import os


#sdate = '2024-10-25/07-55-15'
#df = read_frontier_buffer(sdate)


### A) random_mutaions
if False:
    # Plot reward vs step for each file
    plt.figure(figsize=(10, 6))

    for file in glob.glob(os.path.join("..", "random_mutations_*.csv")):
        df = pd.read_csv(file)
        df.columns = ['step', 'reward', 'max_reward']
        plt.plot(df['step'], df['max_reward'], label=os.path.basename(file))

    plt.xlabel('Step')
    #plt.ylabel('Reward')
    plt.ylabel('Max Reward')
    plt.title('Reward vs Step for Random Mutations')
    plt.xlim(0, 1000)
    plt.legend()
    plt.show()

## analyze directed evolution
if True:
    plt.figure(figsize=(10, 6))

    for file in glob.glob(os.path.join("..", "out_directed_evolution_*.csv")):
        df = pd.read_csv(file)
        df.columns = ['step', 'reward', 'max_reward']
        #plt.plot(df['step'], df['reward'], label=os.path.basename(file))
        plt.plot(df['step'], df['max_reward'], label=os.path.basename(file))

    plt.xlabel('Step')
    plt.ylabel('Reward')
    plt.ylabel('Max Reward')
    plt.title('Reward vs Step for Directed Evolution')
    plt.xlim(0, 1000)
    plt.legend()
    plt.show()

# analyze frontier buffer



