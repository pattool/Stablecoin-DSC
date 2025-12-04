# pragma version 0.4.1

# ------------------------------------------------------------------
#                             NATSPEC
# ------------------------------------------------------------------
"""
@license MIT
@title Decentralized Stable Coin
@author Patrick Pekel
@notice  My first stable coin
@dev Follows the ERC20 token standard
"""


# ------------------------------------------------------------------
#                BUILT-IN INTERFACE OF THE VYPER COMPILER
# ------------------------------------------------------------------
# @dev We import and implement the `IERC20` interface,
# which is a built-in interface of the Vyper compiler.
#from ethereum.ercs import IERC20
#implements: IERC20  # Does not compile before it Ads all the function of an interface!


# ------------------------------------------------------------------
#                        IMPORT LIBRARIES
# ------------------------------------------------------------------
from snekmate.auth import ownable as ow
from snekmate.tokens import erc20
from contracts.interfaces import i_decentralized_stable_coin


# ------------------------------------------------------------------
#                      IMPORT STORAGE VARIABLES
# ------------------------------------------------------------------
implements: i_decentralized_stable_coin
initializes: ow
initializes: erc20[ownable := ow] # uses the exactly ownable as we imported as ow


# ------------------------------------------------------------------
#                         Constant VARIABLES
# ------------------------------------------------------------------
NAME: constant(String[25]) = "Decentralized Stable Coin"
SYMBOL: constant(String[5]) = "DSC"
DECIMALS: constant(uint8) = 18
EIP712_VERSION: constant(String[20]) = "1"


# ------------------------------------------------------------------
#                         EXPORTS (find in the snekmate lib:tokens)
# ------------------------------------------------------------------
exports: (
    erc20.IERC20,
    erc20.burn_from,
    erc20.mint,
    erc20.set_minter,
    ow.owner,
    ow.transfer_ownership
)


# ------------------------------------------------------------------
#                           CONSTRUCTOR
# ------------------------------------------------------------------
@deploy
def __init__():
    ow.__init__()
    erc20.__init__(NAME, SYMBOL, DECIMALS, NAME, EIP712_VERSION)

