import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.helpers.test_inf_BIND import get_reward
import numpy as np
from datetime import datetime
from tqdm import tqdm
import hydra
from omegaconf import DictConfig

# 1. we start with the wildtype
config_file = "conf_default.yaml" # located in /usw/rl-enzyme-engineering/
hydra.initialize(config_path="..") # must be relative to this files directory, not cwd!
cfg = hydra.compose(config_name=config_file.split('.')[0])
wildtype, smile = cfg.experiment.wildtype_AA_seq, cfg.experiment.ligand_smile

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
out_file = f"out_directed_evolution_{timestamp}.csv"
n_generations = 30

def get_top_sequences(population, population_scores, n_top):
    return [sequence for _, sequence in sorted(zip(population_scores, population), reverse=True)[:n_top]]

def run_directed_evolution(n_generations, wildtype, smile, out_file):
    max_reward = 0
    population = [wildtype]
    population_scores = [get_reward(wildtype, smile)]
    iStep = 0
    for _ in tqdm(range(n_generations)):
        new_population_scores = []
        new_population = []
        for sequence in get_top_sequences(population, population_scores, cfg.frontier_buffer.n_top):
            for _1 in range( cfg.on_policy_trainer.epochs ): # start with same sequence several times 
                for _2 in range( cfg.on_policy_trainer.steps_per_epoch * cfg.on_policy_trainer.epochs ):
                    # new mutation  
                    i = np.random.randint(0, len(sequence))
                    aa = np.random.choice(list('ACDEFGHIKLMNPQRSTVWY'))
                    sequence = sequence[:i] + aa + sequence[i+1:]
                    new_population.append(sequence)
                    # get reward
                    reward = get_reward(sequence, smile)
                    new_population_scores.append(reward)
                    # save to file
                    max_reward = max(max_reward, reward)
                    iStep += 1
                    with open(out_file, 'a') as f:
                        f.write(f"{iStep},{reward},{max_reward}\n")
        # update population
        population = new_population
        population_scores = new_population_scores
        pass
    return

if __name__ == '__main__':
    run_directed_evolution(n_generations, wildtype, smile, out_file)