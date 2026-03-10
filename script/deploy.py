from script.deploy_dsc import deploy_dsc
from script.deploy_dsc_engine import deploy_dsc_engine


def moccasin_main():
    """Entry point: deploy the DSC token and DSCEngine in sequence,
    passing the DSC contract to the engine for ownership and minting rights."""
    
    dsc = deploy_dsc()
    deploy_dsc_engine(dsc)
    