from contracts import decentralized_stable_coin
from moccasin.boa_tools import VyperContract

def deploy_dsc() -> VyperContract:
    return decentralized_stable_coin.deploy()


def moccasin_main() -> VyperContract:
    return deploy_dsc()