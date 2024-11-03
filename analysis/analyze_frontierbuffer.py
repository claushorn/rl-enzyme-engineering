import numpy as np
import pandas as pd
import pickle
import matplotlib.pyplot as plt
import os, sys
import tqdm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.helpers import this_package_path
from sklearn.manifold import TSNE

sdate = '2024-10-24/14-03-47'
sdate = '2024-10-25/10-18-18'
i_generation = 0

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
df = load_data()

# print mean, and max scores for each generation
for i_generation in sorted(df['generation'].unique()):
    scores = df[df['generation'] == i_generation]['scores']
    scores = np.array(scores)
    print(f'Generation {i_generation}: mean score = {np.mean(scores)}, max score = {np.max(scores)}, # sequences = {len(scores)}')

if False:
    # scores histogram, color by generation
    for i_generation in df['generation'].unique():
        scores = df[df['generation'] == i_generation]['scores']
        scores = np.array(scores)
        plt.hist(scores, bins=100, alpha=0.4, label=f'generation {i_generation}')
    plt.legend()
    plt.xlabel('Score')
    plt.ylabel('# sequences')
    plt.show()

if False:
    # counts histogram, color by generation
    for i_generation in df['generation'].unique():
        counts = df[df['generation'] == i_generation]['counts']
        counts = np.array(counts)
        plt.hist(counts, bins=100, alpha=0.4, label=f'generation {i_generation}')
    plt.legend()
    plt.xlabel('# times sequence was sampled')
    plt.ylabel('# sequences')
    plt.show()

if False:
    # scores vs counts
    for i_generation in df['generation'].unique():
        scores = df[df['generation'] == i_generation]['scores']
        counts = df[df['generation'] == i_generation]['counts']
        plt.scatter(scores, counts, alpha=0.4, label=f'generation {i_generation}')
    plt.legend()
    plt.xlabel('Score')
    plt.ylabel('# times sequence was sampled')
    plt.show()



# Levenshtein distance in Python using dynamic programming.
# Levenshtein distance: Handles insertions, deletions, and substitutions; applicable for sequences of different lengths.
# Hamming distance: Only handles substitutions; applicable for sequences of the same length.

import Levenshtein
from tqdm import tqdm

# calculate distance matrix of sequences
def pairwise_levenshtein(sequences):
    n = len(sequences)
    # Create an empty distance matrix
    distance_matrix = np.zeros((n, n))
    
    # Compute the Levenshtein distance for all pairs of sequences
    for i in tqdm(range(n)):
        for j in range(i, n):  # Only calculate for upper triangle and mirror later
            if i == j:
                distance_matrix[i][j] = 0  # Distance between the same sequence is 0
            else:
                dist = Levenshtein.distance(sequences[i], sequences[j])
                distance_matrix[i][j] = dist
                distance_matrix[j][i] = dist  # Mirror the distance since it's symmetric

    return distance_matrix

if False:
    # plot distance matrix
    sequences = df['sequences'].values
    distance_matrix = pairwise_levenshtein(sequences)
    plt.imshow(distance_matrix)
    plt.colorbar()
    plt.show()


def plot_clusters_MD(distance_matrix, i_generation):
    from sklearn.manifold import MDS
    # Apply MDS to project the distances into 2D
    mds = MDS(n_components=2, dissimilarity="precomputed", random_state=42)
    points_2d = mds.fit_transform(distance_matrix)

    # Plot the 2D points
    plt.figure(figsize=(8, 6))
    plt.scatter(points_2d[:, 0], points_2d[:, 1], c='blue', s=100)

    plt.title(f"2D MD projection of sequences based on Levenshtein distance - Generation {i_generation}")
    plt.xlabel("Component 1")
    plt.ylabel("Component 2")
    #plt.grid(True)
    plt.show()

def plot_clusters_tSNE(distance_matrix, i_generation=None):
    from sklearn.manifold import TSNE
    # Apply t-SNE to project the distances into 2D
    tsne = TSNE(n_components=2)
    points_2d = tsne.fit_transform(distance_matrix)

    # Plot the 2D points
    plt.figure(figsize=(8, 6))
    plt.scatter(points_2d[:, 0], points_2d[:, 1], c='blue', s=100)

    stitle = f"2D t-SNE projection of sequences based on Levenshtein distance" 
    if i_generation:
        stitle += f" - Generation {i_generation}"
    plt.title(stitle)
    plt.xlabel("Component 1")
    plt.ylabel("Component 2")
    #plt.grid(True)
    plt.show()

if False:
    for i_generation in df['generation'].unique():
        sequences = df[df['generation'] == i_generation]['sequences']
        distance_matrix = pairwise_levenshtein(sequences)
        #plot_clusters_MD(distance_matrix, i_generation)
        plot_clusters_tSNE(distance_matrix, i_generation)

def plot_clusters_tSNE_all(distance_matrix, generations, scores):
    # Perform t-SNE to reduce the distance matrix to 2D
    tsne = TSNE(n_components=2)
    points_2d = tsne.fit_transform(distance_matrix)
    
    # Normalize scores for coloring
    norm = plt.Normalize(scores.min(), scores.max())
    cmap = plt.get_cmap('viridis')
    
    # Define markers for different generations
    markers = ['o', 's', 'D', '^', 'v', '<', '>', 'p', '*', 'h', 'H', 'x', 'd', '|', '_']
    unique_generations = np.unique(generations)
    marker_dict = {gen: markers[i % len(markers)] for i, gen in enumerate(unique_generations)}
    
    plt.figure(figsize=(10, 8))
    
    # Plot each point with the corresponding marker and color
    for gen in unique_generations:
        idx = np.where(generations == gen)[0]  # Convert to list of indices
        plt.scatter(points_2d[idx, 0], points_2d[idx, 1], 
                    c=scores.iloc[idx], cmap=cmap, norm=norm, 
                    marker=marker_dict[gen], label=f'Generation {gen}', s=100, edgecolor='k')
    
    plt.colorbar(label='Score')
    plt.title("2D t-SNE projection of sequences based on Levenshtein distance")
    plt.xlabel("Component 1")
    plt.ylabel("Component 2")
    plt.legend()
    plt.show()


if True:
    dfT = df[df['generation'].isin([0,4,8,12,16,20])]
    sequences = dfT['sequences'].tolist()
    scores = dfT['scores']
    generation = dfT['generation']
    distance_matrix = pairwise_levenshtein(sequences)
    #plot_clusters_MD(distance_matrix, i_generation)
    plot_clusters_tSNE_all(distance_matrix, generation, scores)





