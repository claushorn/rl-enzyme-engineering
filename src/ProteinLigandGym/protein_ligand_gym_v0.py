from ProteinLigandGym.env.protein_ligand_gym import ProteinLigandInteractionEnv

def env(render_mode=None,
        wildtype_aa_seq: str = 'AA',
        ligand_smile: str = 'SMILE',
        device = 'cuda',
        config={}):
    """
    The env function often wraps the environment in wrappers by default.
    You can find full documentation for these methods
    elsewhere in the developer documentation.
    """
    
    env = ProteinLigandInteractionEnv(render_mode, wildtype_aa_seq, ligand_smile, device, config)

    return env