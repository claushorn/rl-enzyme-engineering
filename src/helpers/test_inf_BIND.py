# %%
import sys, os, time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from helpers import this_package_path
sys.path.append(this_package_path() + "/rl-enzyme-engineering/src")
sys.path.append(this_package_path() + "/rl-enzyme-engineering/src/ProteinLigandGym/env/models")
sys.path.append(this_package_path() + "/rl-enzyme-engineering/src/ProteinLigandGym/env/models/BIND")
from ProteinLigandGym.env.bind_inference import init_BIND, predict_binder
import hydra
from omegaconf import DictConfig

#device = 'cuda'
device = 'cpu'

bind_model, esm_model, esm_tokeniser, _, _ = init_BIND(device)

sequence = "MSTETLRLQKARATEEGLAFETPGGLTRALRDGCFLLAVPPGFDTTPGVTLCREFFRPVEQGGESTRAYRGFRDLDGVYFDREHFQTEHVLIDGPGRERHFPPELRRMAEHMHELARHVLRTVLTELGVARELWSEVTGGAVDGRGTEWFAANHYRSERDRLGCAPHKDTGFVTVLYIEEGGLEAATGGSWTPVDPVPGCFVVNFGGAFELLTSGLDRPVRALLHRVRQCAPRPESADRFSFAAFVNPPPTGDLYRVGADGTATVARSTEDFLRDFNERTWGDGYADFGIAPPEPAGVAEDGVRA"
#smile = "CC(=O)CCc1ccc2OCOc2c1"
smile = "c1(ccc(cc1)c1ccccc1c1[n-]nnn1)Cn1c(c(nc1CCCC)Cl)CO"

if __file__  == '__main__':
    start_time = time.time()
    for i in range(20): 
        scores = predict_binder(bind_model, esm_model, esm_tokeniser, device, [sequence], smile)
    end_time = time.time()
    print(f"Execution time: {end_time - start_time} seconds") # ~0.5 sec per call
    print(scores)

def get_reward(sequence, smile):
    scores = predict_binder(bind_model, esm_model, esm_tokeniser, device, [sequence], smile)
    return 1.0 - float(scores[0]['non_binder_prob'])

