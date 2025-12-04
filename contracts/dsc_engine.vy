# pragma version 0.4.1

# ------------------------------------------------------------------
#                             NATSPEC
# ------------------------------------------------------------------
"""
@license MIT
@title DSCEngine
@author Patrick Pekel
@notice 
    Collateral: Exogenous (WETH, WBTC, etc..)
    Minting (Stability) Mechanism: Decentralized (Algorithmic)
    Value (Relative Stability): Anchored (pegged to USD)
    Collateral Type: Crypto
"""


# ------------------------------------------------------------------
#                             IMPORTS
# ------------------------------------------------------------------
# Handle collateral tokens: WETH, WBTC contracts
from ethereum.ercs import IERC20

# Control your DSC token
from contracts.interfaces import i_decentralized_stable_coin

# Get price data: Chainlink price feeds
from contracts.interfaces import AggregatorV3Interface 


# ------------------------------------------------------------------
#                             CONSTANT
# ------------------------------------------------------------------
ADDITIONAL_FEE_PRECISION: public(constant(uint256)) = 1 * (10 ** 10)
PRECISION: public(constant(uint256)) = 1 * (10 ** 18)
LIQUIDATION_TRESHOLD: public(constant(uint256)) = 50
LIQUIDATION_PRECISION: public(constant(uint256)) = 100
LIQUIDATION_BONUS: public(constant(uint256)) = 10
MIN_HEALTH_FACTOR: public(constant(uint256)) = 1 * (10 ** 18)


# ------------------------------------------------------------------
#                            IMMUTABLES
# ------------------------------------------------------------------
DSC: public(immutable(i_decentralized_stable_coin))
COLLATERAL_TOKENS: public(immutable(address[2]))


# ------------------------------------------------------------------
#                        STORAGE VARIABLES
# ------------------------------------------------------------------

# Track which Chainlink oracle to use for each token's price
token_to_price_feed: public(HashMap[address, address]) 

# Track each user's collateral holdings separately.  user          token    amount
user_to_token_to_amount_deposited: public(HashMap[address, HashMap[address, uint256]])

# Track each user's debt (how much DSC they owe)
user_to_dsc_minted: public(HashMap[address, uint256]) 


# ------------------------------------------------------------------
#                              EVENTS
# ------------------------------------------------------------------
event CollateralDeposited:
    user: indexed(address)
    amount: indexed(uint256)


event CollateralRedeem:
    token: indexed(address)
    amount: indexed(uint256)
    _from: address
    _to: address


# ------------------------------------------------------------------
#                           CONSTRUCTOR
# ------------------------------------------------------------------
@deploy
def __init__(
    token_addresses: address[2], 
    price_feed_addresses: address[2], 
    dsc_address: address
):
    """
    @notice Initialize the DSCEngine with collateral tokens and price feed
    @dev Sets up the mapping between collateral tokens and their Chainlink price feeds
    @param token_addresses Array containing WETH and WBTC token addresses
    @param price_feed_addresses Array containing corresponding Chainlink price feed addresses
    @param dsc_address Address of the Decentralized Stable Coin (DSC) contract
    """
    DSC = i_decentralized_stable_coin(dsc_address)
    COLLATERAL_TOKENS = token_addresses
    # This is gas inefficient, better Dynarrays!
    self.token_to_price_feed[token_addresses[0]] = price_feed_addresses[0]
    self.token_to_price_feed[token_addresses[1]] = price_feed_addresses[1]


# ------------------------------------------------------------------
#                        EXTERNAL FUNCTIONS
# ------------------------------------------------------------------
# User calls this function
@external
def deposit_collateral(token_collateral_address: address, amount_collateral: uint256):
    """
    @notice Deposit collateral into the protocol
    @dev Transfers collateral tokens from user to this contract and updates internal accounting
    @param token_collateral_address address of the collateral token to deposit (WETH or WBTC)
    @param amount_collateral amount of token to deposit
    """
    self._deposit_collateral(token_collateral_address, amount_collateral)


@external
def deposit_and_mint(token_collateral_address: address, amount_collateral: uint256, amount_dsc: uint256):
    """
    @notice Deposit collateral and mint DSC in a single transaction
    @dev Combines deposit_collateral and mint_dsc operations for gas efficiency
    @param token_collateral_address Address of the collateral token to deposit
    @param amount_collateral Amount of collateral to deposit
    @param amount_dsc Amount of DSC to mint
    """
    self._deposit_collateral(token_collateral_address, amount_collateral)
    self._mint_dsc(amount_dsc)


@external
def mint_dsc(amount: uint256):
    """
    @notice Mint DSC tokens against deposited collateral
    @dev Reverts if minting would break the user's health factor
    @param amount Amount of DSC to mint
    """
    self._mint_dsc(amount)


@external
def redeem_collateral(token_collateral_address: address, amount: uint256):
    """
    @notice Redeem collateral from the protocol
    @dev Reverts if redemption would break the user's health factor
    @param token_collateral_address Address of the collateral token to redeem
    @param amount Amount of collateral to redeem
    """
    self._redeem_collateral(token_collateral_address, amount, msg.sender, msg.sender)
    self._revert_if_health_factor_broken(msg.sender)
    

@external
def redeem_for_dsc(token_collateral: address, amount_collateral: uint256, amount_dsc: uint256):
    """
    @notice Burn DSC and redeem collateral in a single transaction
    @dev Burns DSC first, then redeems collateral, and checks health factor
    @param token_collateral Address of the collateral token to redeem
    @param amount_collateral Amount of collateral to redeem
    @param amount_dsc Amount of DSC to burn
    """
    self._burn_dsc(amount_dsc, msg.sender, msg.sender)
    self._redeem_collateral(token_collateral, amount_collateral, msg.sender, msg.sender)
    self._revert_if_health_factor_broken(msg.sender)


@external
def burn_dsc(amount: uint256):
    """
    @notice Burn DSC tokens to reduce debt
    @dev Updates user's DSC minted balance and burns tokens from circulation
    @param amount Amount of DSC to burn
    """
    self._burn_dsc(amount, msg.sender, msg.sender)
    self._revert_if_health_factor_broken(msg.sender)


@external
def liquidate(collateral: address, user: address, debt_to_cover: uint256):
    """
    @notice Liquidate an undercollateralized position
    @dev Liquidator pays off user's debt and receives collateral plus a bonus
         The liquidated user's health factor must be below MIN_HEALTH_FACTOR
         The liquidation must improve the user's health factor
    @param collateral Address of the collateral token to seize
    @param user Address of the user to liquidate
    @param debt_to_cover Amount of DSC debt to cover
    """
    assert debt_to_cover > 0, "DSCEngine: Needs more than zero"
    starting_health_factor: uint256 = self._health_factor(user)
    assert starting_health_factor < MIN_HEALTH_FACTOR, "DSCEngine: Health factor is good"

    token_amount_from_debt_covered: uint256 = self._get_token_amount_from_usd(collateral, debt_to_cover)
    bonus_collateral: uint256 = (token_amount_from_debt_covered * LIQUIDATION_BONUS) // LIQUIDATION_PRECISION

    self._redeem_collateral(collateral, token_amount_from_debt_covered + bonus_collateral, user, msg.sender)
    self._burn_dsc(debt_to_cover, user, msg.sender)

    ending_health_factor: uint256 = self._health_factor(user)
    assert ending_health_factor > starting_health_factor, "DSCEngine: Didn't improve health factor"
    self._revert_if_health_factor_broken(msg.sender)


@external
def get_account_information(user: address) -> (uint256, uint256):
    """
    @notice Get user's account information
    @dev Returns the total DSC minted and total collateral value for a user
    @param user Address of the user to query
    @return total_dsc_minted Total DSC debt of the user
    @return collateral_value_usd Total collateral value in USD (18 decimals)
    """
    return self._get_account_information(user)


@external
@view
def get_token_amount_from_usd(token: address, usd_amount_in_wei: uint256) -> uint256:
    """
    @notice Convert USD amount to token amount
    @dev Uses Chainlink price feed to calculate token amount from USD value
    @param token Address of the token
    @param usd_amount_in_wei USD amount with 18 decimals
    @return Token amount corresponding to the USD value
    """
    return self._get_token_amount_from_usd(token, usd_amount_in_wei)


@external
@view
def get_usd_value(token: address, amount: uint256) -> uint256:
    """
    @notice Get USD value of a token amount
    @dev Uses Chainlink price feed to calculate USD value
    @param token Address of the token
    @param amount Amount of tokens
    @return USD value with 18 decimals
    """
    return self._get_usd_value(token, amount)


@external
def calculate_health_factor(total_dsc_minted: uint256, total_collateral_value_usd: uint256) -> uint256:
    """
    @notice Calculate health factor from given values
    @dev Health factor = (collateral * liquidation_threshold) / total_dsc_minted
         A health factor below 1e18 means the position can be liquidated
    @param total_dsc_minted Total DSC minted by user
    @param total_collateral_value_usd Total collateral value in USD (18 decimals)
    @return Health factor with 18 decimals (1e18 = 100%)
    """
    return self._calculate_health_factor(total_dsc_minted, total_collateral_value_usd)


@external
def health_factor(user: address) -> uint256:
    """
    @notice Get user's current health factor
    @dev A health factor below 1e18 means the position can be liquidated
    @param user Address of the user to query
    @return Health factor with 18 decimals (1e18 = 100%)
    """
    return self._health_factor(user)


@external
@view
def get_collateral_balance_of_user(user: address, token_collateral: address) -> uint256:
    """
    @notice Get user's collateral balance for a specific token
    @param user Address of the user to query
    @param token_collateral Address of the collateral token
    @return Amount of collateral deposited by the user
    """
    return self.user_to_token_to_amount_deposited[user][token_collateral]


# ------------------------------------------------------------------
#                        INTERNAL FUNCTIONS
# ------------------------------------------------------------------
@internal
def _deposit_collateral(token_collateral_address: address, amount_collateral: uint256):
    """
    @notice Internal function to handle collateral deposits
    @dev Follows CEI pattern: Checks, Effects, Interactions
    @param token_collateral_address Address of the collateral token
    @param amount_collateral Amount of collateral to deposit
    """
    # Checks
    assert amount_collateral > 0, "DSCEngine: Needs more than zero"
    assert self.token_to_price_feed[token_collateral_address] != empty(address), "DSCEngine: Token not supported"
        
    # Effects (Internal)
    self.user_to_token_to_amount_deposited[msg.sender][
        token_collateral_address] += amount_collateral
    # update storage
    log CollateralDeposited(user=msg.sender, amount=amount_collateral)

    # Interactions (External)
    # Need IERC20 to call transferFrom on WETH/WBTC
    success: bool = extcall IERC20(token_collateral_address).transferFrom(
        msg.sender,       # FROM: User's address (0x123...)
        self,             # TO: DSCEngine contract address (0xc0E0bc...)
        amount_collateral
    )
    assert success, "DSCEngine: Transfer failed"
    # Now DSCEngine contract HOLDS the WETH as collateral


@internal
def _redeem_collateral(token_collateral_address: address, amount: uint256, _from: address, _to: address):
    """
    @notice Internal function to handle collateral redemption
    @dev Updates user balance and transfers collateral tokens
    @param token_collateral_address Address of the collateral token
    @param amount Amount of collateral to redeem
    @param _from Address whose collateral balance will be reduced
    @param _to Address that will receive the collateral tokens
    """
    self.user_to_token_to_amount_deposited[_from][token_collateral_address] -= amount
    log CollateralRedeem(token=token_collateral_address, amount=amount, _from=msg.sender, _to=msg.sender)

    # Need IERC20 to call transfer on WETH/WBTC
    succes: bool = extcall IERC20(token_collateral_address).transfer(_to, amount)
    assert succes, "DSCEngine: Transfer failed"


@internal
def _mint_dsc(amount_dsc_to_mint: uint256):
    """
    @notice Internal function to mint DSC tokens
    @dev Updates user's minted balance, checks health factor, then mints tokens
    @param amount_dsc_to_mint Amount of DSC to mint
    """
    assert amount_dsc_to_mint > 0, "DSCEngine: Needs more than zero"
    self.user_to_dsc_minted[msg.sender] += amount_dsc_to_mint

    # Revert't mint_dsc if ratio is broken
    self._revert_if_health_factor_broken(msg.sender)

    # Need i_decentralized_stable_coin to call mint
    extcall DSC.mint(msg.sender, amount_dsc_to_mint)


@internal
def _revert_if_health_factor_broken(user: address):
    """
    @notice Check if user's health factor is below minimum threshold
    @dev Reverts if health factor < MIN_HEALTH_FACTOR (1e18)
    @param user Address of the user to check
    """
    user_health_factor: uint256 = self._health_factor(user)
    assert user_health_factor >= MIN_HEALTH_FACTOR, "DSCEngine: Health factor broken"


@internal
def _get_account_information(user: address) -> (uint256, uint256):
    """
    @notice returns the total DSC minted, and the total value collateral deposited
    @param user Address of the user to query
    @return total_dsc_minted Total DSC debt of the user
    @return collateral_value_usd Total collateral value in USD (18 decimals)
    """
    total_dsc_minted: uint256 = self.user_to_dsc_minted[user] # value dsc minted in $
    collateral_value_usd: uint256 = self._get_account_collateral_value(user)
    return total_dsc_minted, collateral_value_usd


@internal
def _get_account_collateral_value(user: address) -> uint256:
    """
    @notice Calculate total USD value of user's collateral across all token types
    @dev Iterates through all collateral tokens and sums their USD values
    @param user Address of the user to query
    @return total_collateral_value_usd Total collateral value in USD (18 decimals)
    """
    total_collateral_value_usd: uint256 = 0
    for token: address in COLLATERAL_TOKENS:
        amount: uint256 = self.user_to_token_to_amount_deposited[user][token]
        total_collateral_value_usd += self._get_usd_value(token, amount)
    return total_collateral_value_usd


@internal
@view
def _get_usd_value(token: address, amount: uint256) -> uint256:
    """
    @notice Convert token amount to USD value using Chainlink price feed
    @dev Chainlink returns prices with 8 decimals, we scale to 18 decimals
    @param token Address of the token
    @param amount Amount of tokens
    @return USD value with 18 decimals
    """
    price_feed: AggregatorV3Interface = AggregatorV3Interface(self.token_to_price_feed[token])
    price: int256 = staticcall price_feed.latestAnswer()
    return ((convert(price, uint256) * ADDITIONAL_FEE_PRECISION) * amount) // PRECISION


@internal
@view
def _get_token_amount_from_usd(token: address, usd_amount_in_wei: uint256) -> uint256:
    """
    @notice Convert USD amount to token amount using Chainlink price feed
    @dev Chainlink returns prices with 8 decimals, USD amount has 18 decimals
    @param token Address of the token
    @param usd_amount_in_wei USD amount with 18 decimals
    @return Token amount
    """
    price_feed: AggregatorV3Interface = AggregatorV3Interface(self.token_to_price_feed[token])
    price: int256 = staticcall price_feed.latestAnswer()
    #return (usd_amount_in_wei * PRECISION) // (convert(price, uint256)) * ADDITIONAL_FEE_PRECISION
    return (usd_amount_in_wei * (10 ** 8)) // (convert(price, uint256))


@internal
def _health_factor(user: address) -> uint256:
    """
    @notice How much DSC they minted and how much collateral they have deposited?
    @dev Health factor = (collateral_value * liquidation_threshold) / dsc_minted
         Returns max uint256 if no DSC is minted
    @param user Address of the user to check
    @return Health factor with 18 decimals (1e18 = 100%)
    """
    total_dsc_minted: uint256 = 0
    total_collateral_value_usd: uint256 = 0
    total_dsc_minted, total_collateral_value_usd = self._get_account_information(user)
    return self._calculate_health_factor(total_dsc_minted, total_collateral_value_usd)


@internal
def _calculate_health_factor(total_dsc_minted: uint256, total_collateral_value_usd: uint256) -> uint256:
    """
    @notice Calculate health factor from DSC minted and collateral value
    @dev If no DSC minted, returns max uint256 (infinite health factor)
         Otherwise: (collateral * 50%) / dsc_minted
         A value below 1e18 means the position is undercollateralized
    @param total_dsc_minted Total DSC minted by user
    @param total_collateral_value_usd Total collateral value in USD (18 decimals)
    @return Health factor with 18 decimals (1e18 = 100%)
    """
    # Only deposited collateral, no minting
    if total_dsc_minted == 0:
        return max_value(uint256)
    # Ratio of DSC minted to collateral value
    collateral_adjusted_for_treshold: uint256 = (total_collateral_value_usd * LIQUIDATION_TRESHOLD) // LIQUIDATION_PRECISION
    return (collateral_adjusted_for_treshold * PRECISION) // total_dsc_minted


@internal
def _burn_dsc(amount: uint256, on_behalf_of: address, dsc_from: address):
    """
    @notice Internal function to burn DSC tokens
    @dev Reduces user's minted balance and burns tokens from circulation
    @param amount Amount of DSC to burn
    @param on_behalf_of Address whose minted balance will be reduced
    @param dsc_from Address from which DSC tokens will be burned
    """
    self.user_to_dsc_minted[on_behalf_of] -= amount

    # Need i_decentralized_stable_coin to call burn_from
    extcall DSC.burn_from(dsc_from, amount)

