import sys
import os
sys.path.append("/root/projects/rl-enzyme-engineering/src/ProteinLigandGym/env/models/BIND/")
sys.path.append("/root/projects/rl-enzyme-engineering/src/ProteinLigandGym/env/models")
sys.path.append("/root/projects/rl-enzyme-engineering/src/ProteinLigandGym/env")
sys.path.append(os.path.abspath(os.path.dirname(__file__))) # cla
from helpers.distance_matrix import DistanceMatrix

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API")
warnings.filterwarnings("ignore", message="`clean_up_tokenization_spaces` was not set")

import signal
import random
import pickle
from copy import copy
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import hydra
from omegaconf import DictConfig, OmegaConf
import logging
import numpy as np
import pandas as pd
import time
import heapq
import torch
from torch import nn
import torch.nn.functional as F
from torch.distributions import Distribution
from torch.utils.tensorboard import SummaryWriter
from torch.distributions import Categorical, Distribution, Independent, Bernoulli
from torch.optim.lr_scheduler import LambdaLR, ReduceLROnPlateau
from ProteinSequencePolicy.policy import ProteinSequencePolicy
from ProteinLigandGym import protein_ligand_gym_v0
from tianshou.data import Collector, VectorReplayBuffer
from tianshou.env import DummyVectorEnv, PettingZooEnv
from tianshou.policy import MultiAgentPolicyManager, RandomPolicy, PPOPolicy
from tianshou.trainer import OnpolicyTrainer
from tianshou.utils.net.common import ActorCritic, Net, MLP
from tianshou.utils.net.discrete import Actor, Critic
from tianshou.utils import TensorboardLogger
from tianshou.utils.logger.base import LOG_DATA_TYPE, BaseLogger
from crossattention_graph_net import CustomGraphNet
from tianshou.data import Batch

logger = logging.getLogger(__name__)

class GumbelSoftmaxDistribution(Distribution):
    
    arg_constraints = {}

    def __init__(self, logits, temperature=1.0):
        super().__init__()
        self.logits = logits
        self.temperature = temperature

    def sample(self, sample_shape=torch.Size()):
        return self.rsample(sample_shape)

    def rsample(self, sample_shape=torch.Size()):
        gumbel_noise = -torch.log(-torch.log(torch.rand_like(self.logits)))
        y_soft = F.softmax((self.logits + gumbel_noise) / self.temperature, dim=-1)
        
        # Straight-through estimator
        index = y_soft.max(-1, keepdim=True)[1]
        y_hard = torch.zeros_like(self.logits).scatter_(-1, index, 1.0)
        ret = y_hard - y_soft.detach() + y_soft
        
        return ret

    def log_prob(self, value):
        # Compute log probability using softmax
        return (F.log_softmax(self.logits, dim=-1) * value).sum(-1)

    def entropy(self):
        return -(F.softmax(self.logits, dim=-1) * F.log_softmax(self.logits, dim=-1)).sum(-1)


class FrontierBuffer:
    _file_ = 'frontier_buffer'
    def __init__(self, n_top: int, wildtype_AA_seq: str):
        self.n_top = n_top
        #self.batch = Batch(seq=None, score=None)
        self.sequences = [wildtype_AA_seq]
        self.scores = [0]
        self.other_scores = [0]
        self.counts = [1]
        self.sequence_to_index = {}  # for fast lookups
        self._load()

    def _load(self):   # TODO loead last generation !!!
        if not os.path.exists(self._file_+".pkl"): 
            print(f"FrontierBuffer: no frontier file found, starting fresh.")
            return
        with open(self._file_, 'rb') as f:
            self.sequences, self.scores, self.counts, self.other_scores = pickle.load(f)

    def save(self, i_generation):
        with open(self._file_+f"_generation{i_generation}.pkl", 'wb') as f:
            pickle.dump((self.sequences,self.scores,self.counts,self.other_scores), f)
        print(f"FrontierBuffer: saved, size: {len(self.sequences)}, top score: {max(self.scores)}")
    
    def add(self, sequence, score, other_scores):
        idx = self.sequence_to_index.get(sequence, -1) # O(1) average-time complexity for lookups
        if idx >= 0: # existing sequence
            self.counts[idx] += 1
        else: # new sequence 
            self.sequences.append(sequence)
            self.scores.append(score)
            self.other_scores.append(other_scores)
            self.counts.append(1)
            self.sequence_to_index[sequence] = len(self.sequences) - 1  

    def remove_allothers(self, indices_tokeep):
        self.sequences = [self.sequences[i] for i in indices_tokeep]
        self.scores = [self.scores[i] for i in indices_tokeep]
        self.counts = [self.counts[i] for i in indices_tokeep]
        self.other_scores = [self.other_scores[i] for i in indices_tokeep]
        self.sequence_to_index = {seq: i for i, seq in enumerate(self.sequences)}

    def top_sequences(self):
        top_indices = heapq.nlargest(self.n_top, range(len(self.scores)), key=lambda i: self.scores[i])
        self.remove_allothers(top_indices)
        return copy(self.sequences) # have to make a copy! 

    def top_sequences_diverse(self, min_distance):
        selected = []
        dm = DistanceMatrix(self.sequences)
        for i in np.argsort(self.scores)[::-1]: # sort by score in descending order
            if dm.diverse(i, selected, min_distance): # min distance 5
                selected.append(i)
                if len(selected) == self.n_top:
                    self.remove_allothers(selected)
                    return copy(self.sequences) # have to make a copy! 
        print(f"FrontierBuffer: WARNING: not enough >{min_distance} sequences found! found {len(selected)} out of {self.n_top}")
        self.remove_allothers(selected)
        return copy(self.sequences) # have to make a copy! 
    
    def top_sequences_diverse_important(self):
        return 
    
    def __len__(self):
        return len(self.sequences)

def run_one_generation(trainer, frontier_buffer, env0, i_generation, cfg: DictConfig):
    for i, top_seq in enumerate(frontier_buffer.top_sequences_diverse(cfg.frontier_buffer.min_diversity_distance)):
        env0.set_sequence( top_seq )
        print(f"run_one_generation: Starting from Top sequence {i}")
        result = trainer.run()
        print("trainer result:",result)
        for seq, score, other_scores in env0.tracker.get_top_sequences():
            frontier_buffer.add(seq, score, other_scores)
    frontier_buffer.save(i_generation)

def run_frontier(trainer, env0, cfg: DictConfig): # loop over generations
    frontier_buffer = FrontierBuffer(cfg.frontier_buffer.n_top, cfg.experiment.wildtype_AA_seq)

    for i_generation in range(cfg.frontier_buffer.max_generations):
        print(f"Generation {i_generation}")
        run_one_generation(trainer, frontier_buffer, env0, i_generation, cfg)
    

def run(cfg: DictConfig):
    
    # Logger
    log_path = os.path.join(os.getcwd(), 'rl-loop')
    writer = SummaryWriter(log_path)
    tb_logger = TensorboardLogger(writer, train_interval=10,update_interval=1)
    
    device = cfg.experiment.device

    logger.debug("Loading PettingZoo environment...")

    # Signal Handler
    def signal_handler(signum, frame):
        if 'env' in locals():
            logger.info("Closing environment...")
            env.close()
        if 'write' in locals():
            logger.info("Closing tensorboard writer...")
            writer.close() # Tensorboard writer
        if device == 'cuda':
            logger.info("Clearing CUDA cache...")
            torch.cuda.empty_cache()
        logger.info("Exiting...")
        sys.exit(0)
            
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Set Seed
    seed = random.randint(0, 2**32 - 1)
    np.random.seed(seed)
    torch.manual_seed(seed)
    tb_logger.write("config", 0, {"seed": seed})
    
    logger.info(f"Steps per episode: {cfg.on_policy_trainer.steps_per_epoch}")

    env = protein_ligand_gym_v0.env(
        render_mode="human",
        wildtype_aa_seq=cfg.experiment.wildtype_AA_seq,
        ligand_smile=cfg.experiment.ligand_smile,
        max_steps=cfg.on_policy_trainer.steps_per_epoch,
        device=device,
        config=cfg,
    )
    seq_encoder = env.encode_aa_sequence
    env0 = env
    env = PettingZooEnv(env)
    
    # Model PPO
    action_shape = env.action_space.shape
    net = CustomGraphNet(
        state_shape=env.observation_space,
        action_shape=env.action_space.shape,
        device=device
    )
    actor = Actor(preprocess_net=net, action_shape=action_shape, softmax_output=False, hidden_sizes=[256, 256, 256], device=device)
    critic = Critic(net, hidden_sizes=[256, 256, 256] ,device=device)
    
    def actor_init(layer):
        if isinstance(layer, nn.Linear):
            torch.nn.init.orthogonal_(layer.weight, 0.01)
            torch.nn.init.constant_(layer.bias, 0.0)

    def critic_init(layer):
        if isinstance(layer, nn.Linear):
            torch.nn.init.orthogonal_(layer.weight, 1)
            torch.nn.init.constant_(layer.bias, 0.0)
            
    actor.last.apply(actor_init)
    critic.last.apply(critic_init)

    optim = torch.optim.Adam(
        ActorCritic(actor, critic).parameters(), lr=cfg.agents.picker_ppo.adam.learning_rate, eps=cfg.agents.picker_ppo.adam.epsilon
    )
    
    def gumbel_dist(logits: torch.Tensor) -> Distribution:
        return GumbelSoftmaxDistribution(logits)
    
    # PPO policy
    ppo_policy: PPOPolicy = PPOPolicy(
        actor=actor,
        critic=critic,
        optim=optim,
        dist_fn=gumbel_dist,
        action_space=env.action_space,
        eps_clip=cfg.agents.picker_ppo.policy.eps,
        dual_clip=None,
        value_clip=cfg.agents.picker_ppo.policy.value_clip,
        advantage_normalization=cfg.agents.picker_ppo.policy.advantage_normalization,
        recompute_advantage=cfg.agents.picker_ppo.policy.recompute_advantage,
        vf_coef=cfg.agents.picker_ppo.policy.vf_coef,
        ent_coef=cfg.agents.picker_ppo.policy.ent_coef,
        max_grad_norm= None, # Don't change!
        gae_lambda=cfg.agents.picker_ppo.policy.gae_lambda,
        discount_factor=cfg.agents.picker_ppo.policy.discount_factor,
        reward_normalization=cfg.agents.picker_ppo.policy.reward_normalization, # 5.1 Value Normalization
        deterministic_eval=False,
        action_scaling=False,
        lr_scheduler=None,
    ).to(device)
    
    buffer = VectorReplayBuffer(
        total_size=cfg.on_policy_trainer.replayBuffer.total_size,
        buffer_num=1,
        ignore_obs_next=True,
        save_only_last_obs=False,
        stack_num=1,
    )

    policy = MultiAgentPolicyManager(
        [
            ppo_policy,
            ProteinSequencePolicy(
                model_size_parameters = cfg.agents.filler_plm.evodiff_model_size_parameters,
                sequence_encoder=seq_encoder,
                action_space=env.action_space,
                device=device
            )
        ],
        env
    )

    env = DummyVectorEnv([lambda: env])

    collector = Collector(
        policy=policy,
        env=env,
        buffer=buffer,
        exploration_noise=False,
    )

    def save_checkpoint_fn(epoch: int, env_step: int, gradient_step: int) -> str:
        # Saves after every epoch
        logger.info("Saving models and buffer.")
        ckpt_path = os.path.join(log_path, "checkpoint.pth")
        torch.save(
            {
                "model": policy.state_dict(),
                "optim": optim.state_dict(),
            },
            ckpt_path,
        )
        # TODO Renable
        #buffer_path = os.path.join(log_path, "train_buffer.pkl")
        #with open(buffer_path, "wb") as f:
        #    pickle.dump(collector.buffer, f)
        return ckpt_path

    def time_limit_reached(elapsed_time, limit_seconds):
        return elapsed_time >= limit_seconds

    start_time = time.time()
    time_limit = cfg.experiment.time_limit_h * 60 * 60

    def stop_fn(epoch, env_step):
        elapsed_time = time.time() - start_time
        return time_limit_reached(elapsed_time, time_limit)
    
    trainer = OnpolicyTrainer(
        policy=policy,
        max_epoch=cfg.on_policy_trainer.epochs,
        batch_size=cfg.on_policy_trainer.batch_size,
        train_collector=collector,
        test_collector=None,
        buffer=None,
        step_per_epoch=cfg.on_policy_trainer.steps_per_epoch,
        repeat_per_collect=cfg.on_policy_trainer.repeat_per_collect,
        episode_per_test=0,
        update_per_step=1.0,
        step_per_collect=cfg.on_policy_trainer.steps_per_collect * 2, # TODO find out why this factor is necessary
        episode_per_collect=None,
        train_fn=None,
        test_fn=None,
        stop_fn=stop_fn,
        save_best_fn=None,
        save_checkpoint_fn=save_checkpoint_fn,
        resume_from_log=False,
        reward_metric=None,
        logger=tb_logger,
        verbose=True,
        show_progress=True,
        test_in_train=True,
        save_fn=None,
    )
    run_frontier(trainer,env0,cfg)


@hydra.main(version_base=None, config_path="../", config_name='conf')
def main(cfg: DictConfig):
    run(cfg)

if __name__ == "__main__":
    main()