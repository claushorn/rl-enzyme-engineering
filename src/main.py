import sys
sys.path.append("/root/projects/rl-enzyme-engineering/src/ProteinLigandGym/env/models/AlphaFlow")
sys.path.append("/root/projects/rl-enzyme-engineering/src/ProteinLigandGym/env/models/FABind/FABind_plus/fabind")
sys.path.append("/root/projects/rl-enzyme-engineering/src/ProteinLigandGym/env/models/DSMBind")
sys.path.append("/root/projects/rl-enzyme-engineering/src/ProteinLigandGym/env/models/BIND/")
sys.path.append("/root/projects/rl-enzyme-engineering/src/ProteinLigandGym/env/models")
sys.path.append("/root/projects/rl-enzyme-engineering/src/ProteinLigandGym/env")

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import hydra
from omegaconf import DictConfig, OmegaConf
import logging
import numpy as np
import pandas as pd
import time
import os
import torch
from torch import nn
from torch.distributions import Categorical, Distribution
from torch.optim.lr_scheduler import LambdaLR
from ProteinSequencePolicy.policy import ProteinSequencePolicy
from ProteinLigandGym import protein_ligand_gym_v0
from tianshou.data import Collector, VectorReplayBuffer
from tianshou.env import DummyVectorEnv, PettingZooEnv
from tianshou.policy import MultiAgentPolicyManager, RandomPolicy, PPOPolicy
from tianshou.trainer import OnpolicyTrainer
from tianshou.utils.net.common import ActorCritic
from tianshou.utils.net.discrete import Actor, Critic
#from common import TrainLogger

logger = logging.getLogger(__name__)

class Net(nn.Module):
    def __init__(self, state_shape, action_shape):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(np.prod(state_shape), 128), nn.ReLU(inplace=True),
            nn.Linear(128, 128), nn.ReLU(inplace=True),
            nn.Linear(128, 128), nn.ReLU(inplace=True),
            nn.Linear(128, np.prod(action_shape)),
        )

    def forward(self, obs, state=None, info={}):
        if not isinstance(obs, torch.Tensor):
            obs = torch.tensor(obs, dtype=torch.float)
        batch = obs.shape[0]
        logits = self.model(obs.view(batch, -1))
        return logits, state




@hydra.main(version_base=None, config_path="../conf/", config_name='conf_dev')
def main(cfg: DictConfig):
    
    device = cfg.experiment.device

    print(OmegaConf.to_yaml(cfg))

    logger.debug("Loading PettingZoo environment...")

    # TODO add seed:
    env = protein_ligand_gym_v0.env(render_mode="human",
                                    wildtype_aa_seq=cfg.experiment.wildtype_AA_seq,
                                    ligand_smile=cfg.experiment.ligand_smile,
                                    device=device,
                                    config=cfg)
    env = PettingZooEnv(env)
    
    # Model PPO
    state_shape = env.observation_space['protein_ligand_conformation_latent'].shape
    action_shape = env.action_space.shape
    print(env.action_space.shape)

    # seed
    # TODO make seed cfg.seed
    seed = 1
    np.random.seed(seed)
    torch.manual_seed(seed)

    net = Net(state_shape, action_shape)
    actor = Actor(net, action_shape, softmax_output=False, device=device)
    critic = Critic(net, device=device)
    
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
        ActorCritic(actor, critic).parameters(), lr=2.5e-4, eps=1e-5
    )
    
    def dist(logits: torch.Tensor) -> Distribution:
        return Categorical(logits=logits)
    
    # decay learning rate to 0 linearly
    step_per_collect = 100
    step_per_epoch = 128 * 8
    epoch = int(10000000 // (128 * 8))
    #lr_scheduler = LambdaLR(optim, lr_lambda=lambda e: 1 - e / epoch)
    
    # PPO policy
    ppo_policy: PPOPolicy = PPOPolicy(
        actor=actor,
        critic=critic,
        optim=optim,
        dist_fn=dist,
        action_space=env.action_space,
        eps_clip=0.2,
        dual_clip=None,
        value_clip=True,
        advantage_normalization=True,
        recompute_advantage=False,
        vf_coef=0.5,
        ent_coef=0.01,
        max_grad_norm=0.5,
        gae_lambda=0.95,
        discount_factor=0.99,
        reward_normalization=False,
        deterministic_eval=False,
        observation_space=env.observation_space,
        action_scaling=False,
        lr_scheduler=None,
        #lr_scheduler=lr_scheduler,
    ).to(device)
    
    buffer = VectorReplayBuffer(
        128 * 8,
        buffer_num=len(env), # TODO validate
        ignore_obs_next=True,
        save_only_last_obs=True,
        stack_num=4,
    )

    policies = MultiAgentPolicyManager(
        [
            #RandomPolicy(),
            ppo_policy(),
            ProteinSequencePolicy(
                action_space=env.action_space,
                device=device
            )
        ],
        env
    )

    env = DummyVectorEnv([lambda: env])

    start_time = time.time()

     # train
    result = OnpolicyTrainer(
        policy=policies,
        max_epoch=epoch,
        batch_size=256,
        train_collector=collector,
        test_collector=None,
        buffer=None,
        step_per_epoch=step_per_epoch,
        repeat_per_collect=4,
        episode_per_test=0,
        update_per_step=1.0,
        step_per_collect=step_per_collect,
        episode_per_collect=None,
        train_fn=None,
        test_fn=None,
        stop_fn=None,
        save_best_fn=None,
        save_checkpoint_fn=None,
        resume_from_log=False,
        reward_metric=None,
        logger=logger,
        verbose=True,
        show_progress=True,
        test_in_train=False,
        save_fn=None,
    ).run()
    
    train_end_time = time.time()

    progress_df = pd.DataFrame(logger.progress_data)
    #progress_df.to_csv(os.path.join(args.path, "progress.csv"), index=False)

    # eval
    collector = Collector(
        policy=policies,
        env=env,
        buffer=VectorReplayBuffer(20_000, len(env)), 
        exploration_noise=False,
    )

    collector = collector.collect(n_episode=1, render=0.1)
    eval_end_time = time.time()
    #args.eval_mean_reward = result.returns_stat.mean
    #args.training_time_h = ((train_end_time - start_time) / 60) / 60
    #args.total_time_h = ((eval_end_time - start_time) / 60) / 60


if __name__ == "__main__":
    main()