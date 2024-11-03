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

sdate = '2024-10-25/07-55-15'
df = read_frontier_buffer(sdate)

print(df.head())
# generation                                          sequences   scores  counts                          other_scores
# 0           8  MSTHTLRLQKLRATEEGLSFELPSSLTRALRDGEFFLAVHPGFDTT...  0.97184       4    (4.52866, 3.961, 3.92619, 4.49457)
print(df.columns)
print(df['generation'].unique())

# filter out non-tuples in other_scores
df = df[df['other_scores'].apply(lambda x: isinstance(x, tuple))]

# plot other_scores[0] vs scores
scores = df['scores']
other_scores = df['other_scores']
#            'pKi': scores[0],
#            'pIC50': scores[1],
#            'pKd': scores[2],
#            'pEC50': scores[3],

other_scores_0 = np.array([x[0] for x in other_scores])
other_scores_1 = np.array([x[1] for x in other_scores])
other_scores_2 = np.array([x[2] for x in other_scores])
other_scores_3 = np.array([x[3] for x in other_scores])

# Create subplots
fig, axs = plt.subplots(2, 2, figsize=(12, 10))

# Plot pKi
axs[0, 0].scatter(scores, other_scores_0)
axs[0, 0].set_xlabel('1 - non-binding-probability')
axs[0, 0].set_ylabel('pKi')
axs[0, 0].yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.2f}'))
axs[0, 0].yaxis.set_major_locator(MultipleLocator(10))

# Plot pIC50
axs[0, 1].scatter(scores, other_scores_1)
axs[0, 1].set_xlabel('1 - non-binding-probability')
axs[0, 1].set_ylabel('pIC50')
axs[0, 1].yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.2f}'))
axs[0, 1].yaxis.set_major_locator(MultipleLocator(10))

# Plot pKd
axs[1, 0].scatter(scores, other_scores_2)
axs[1, 0].set_xlabel('1 - non-binding-probability')
axs[1, 0].set_ylabel('pKd')
axs[1, 0].yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.2f}'))
axs[1, 0].yaxis.set_major_locator(MultipleLocator(10))

# Plot pEC50
axs[1, 1].scatter(scores, other_scores_3)
axs[1, 1].set_xlabel('1 - non-binding-probability')
axs[1, 1].set_ylabel('pEC50')
axs[1, 1].yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.2f}'))
axs[1, 1].yaxis.set_major_locator(MultipleLocator(10))

# Limit y-axis ticks to 0.01 precision
formatter = FuncFormatter(lambda x, _: f'{x:.2f}')
plt.gca().yaxis.set_major_formatter(formatter)
# Set y-axis ticks to have steps of 10
plt.gca().yaxis.set_major_locator(MultipleLocator(100))

# Adjust layout
plt.tight_layout()
plt.show()




