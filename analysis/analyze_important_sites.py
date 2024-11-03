# On average ofver top_sequences of many generations, what is the 1D, 2D importance of sites?

# Uses files produced by analyze_importances.py

from matplotlib import pyplot as plt
import numpy as np
import pickle

total_importance = 0.53478  # for this particular top_sequence !

# 1) 1D importances vs site
with open('importances1D.pkl', 'rb') as f:
   importances1D = pickle.load(f)

if False:
    # make a bar plot
    importances1D_pct = [100*f/total_importance for f in importances1D]
    plt.bar(range(len(importances1D_pct)), importances1D_pct)
    plt.xlabel('Site')
    plt.ylabel('Importance (% of total)')
    plt.title('Effects of Single Mutations')
    plt.show()


# 2) 2D importances vs site
with open('doubleMutation_array.pkl', 'rb') as f:
   doubleMutation_array = pickle.load(f)

filtered = doubleMutation_array.flatten()
filtered = filtered[filtered != 0]
filtered_pct = [100*f/total_importance for f in filtered]

if False:
    # plot histogram of 2D importances from the array
    plt.hist(filtered_pct, bins=30)
    plt.title('Histogram of Mutation-Pair Effects in top_sequence')
    plt.xlabel('Importance Value (% of total)')
    plt.ylabel('Frequency')
    plt.show()


if False:  # 2D importances vs site
    number_strong2d_mutations_perSite = [0]*len(doubleMutation_array)
    for i in range(len(doubleMutation_array)):
        for j in range(len(doubleMutation_array)):
            if 100*doubleMutation_array[i][j]/total_importance > 5: # >5 pct 
                number_strong2d_mutations_perSite[i] += 1
                number_strong2d_mutations_perSite[j] += 1

    # make a bar plot
    plt.bar(range(len(number_strong2d_mutations_perSite)), number_strong2d_mutations_perSite)
    plt.xlabel('Site')
    plt.ylabel('# of Pair-Mutations with >5% Importance')
    plt.title('Effects of Pair-Mutations')
    plt.show()

if False:  # plot doubleMutation_array as a heatmap
    plt.imshow(100*doubleMutation_array/total_importance, cmap='hot', interpolation='nearest')
    plt.colorbar()
    plt.title('Mutation-Pairs Effects')
    plt.show()


doubleMutation_array_extra = np.zeros_like(doubleMutation_array)
for i in range(len(doubleMutation_array)):
    for j in range(i+1, len(doubleMutation_array)):
        if doubleMutation_array[i][j] != 0:
            combinatorial_advantage = (doubleMutation_array[i][j] - importances1D[i] - importances1D[j])
            doubleMutation_array_extra[i][j] = combinatorial_advantage 

plt.imshow(100*doubleMutation_array_extra/total_importance, cmap='hot', interpolation='nearest')
plt.colorbar()
plt.title('Mutation-Pairs Combinatorial Advantage')
plt.show()
            
            
