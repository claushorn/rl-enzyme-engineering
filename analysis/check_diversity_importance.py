from read_frontier_buffer import read_frontier_buffer
import os, sys
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.helpers.distance_matrix import DistanceMatrix
import matplotlib.pyplot as plt

def get_distances(sequences):
    dm = DistanceMatrix(sequences)
    ldist = []
    for i in range(len(sequences)):
        for j in range(i+1, len(sequences)):
            ldist.append( dm.dist(i, j) )
    return ldist

df = read_frontier_buffer("2024-10-25/07-55-15")

if False:
    # print average distance/diversity for each generation
    for i_generation in sorted(df['generation'].unique()):
        sequences = df[df['generation'] == i_generation]['sequences']
        print(f'Generation {i_generation}: # sequences = {len(sequences)}')
        ldist = get_distances(sequences)
        print(f'Generation {i_generation}: average distance = {sum(ldist) / len(ldist)}')

if False:
    # Plot distances for generations 0 to 5
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()

    for i_generation in range(6):
        sequences = df[df['generation'] == i_generation]['sequences']
        print(f'Generation {i_generation}: # sequences = {len(sequences)}')
        ldist = get_distances(sequences)

        # Plot histogram of distances in the corresponding subplot
        ax = axes[i_generation]
        ax.hist(ldist, bins=max(ldist))
        ax.set_xlabel('Distance')
        ax.set_ylabel('# sequence pairs')
        ax.set_title(f'Generation {i_generation}')
        ax.set_xlim(0,80)

    # Adjust layout
    plt.tight_layout()
    plt.show()

if False:
    # test  of  top_sequences_diverse()
    def top_sequences_diverse(sequences, scores, min_distance, n_top):
        selected = []
        dm = DistanceMatrix(sequences)
        for i in np.argsort(scores)[::-1]: # sort by score in descending order
            if dm.diverse(i, selected, min_distance): # min distance 5
                selected.append(i)
                if len(selected) == n_top:
                    return [sequences[i] for i in selected]
        print(f"FrontierBuffer: WARNING: not enough diverse sequences found! found {len(selected)} out of {n_top}")
        return [sequences[i] for i in selected]

    i_generation = 1 
    sequences = df[df['generation'] == i_generation]['sequences']
    scores = df[df['generation'] == i_generation]['scores']
    l = top_sequences_diverse(sequences,scores, 8, 10)
    print(len(l))

