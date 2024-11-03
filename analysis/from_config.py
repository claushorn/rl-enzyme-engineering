import hydra
from omegaconf import DictConfig
import warnings
import os, sys
from src.helpers import this_package_path
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)


def get_wildtype_smile(config_file="conf_default.yaml", sdate_experiment=None): # e.g. sdate = '2024-10-29/09-37-37'
    if sdate_experiment is None:  # works if running in /src or /analysis
        sExperimentOutputPathRelative = ".."  # to go from /rl-enzyme-engineering/analysis to /rl-enzyme-engineering/
    else:
        sExperimentOutputPathRelative = this_package_path()+f'/rl-enzyme-engineering/experiments/{sdate_experiment}/'
    hydra.initialize(config_path=sExperimentOutputPathRelative, version_base=None) # must be relative to the current working directory
    cfg = hydra.compose(config_name=os.path.basename(config_file).split('.')[0])
    wildtype, smile = cfg.experiment.wildtype_AA_seq, cfg.experiment.ligand_smile
    return wildtype, smile


