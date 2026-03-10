from contracts import decentralized_stable_coin
from moccasin.boa_tools import VyperContract

def deploy_dsc() -> VyperContract:
    """Deploy the Decentralized Stable Coin (DSC)
    ERC20 token contract on the active network."""
    
    return decentralized_stable_coin.deploy()


def moccasin_main() -> VyperContract:
    """Entry point: deploy the DSC token
    and return the contract instance."""
    
    return deploy_dsc()