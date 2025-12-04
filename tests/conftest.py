import boa
import pytest
from moccasin.config import get_active_network
from script.deploy_dsc_engine import deploy_dsc_engine
from eth_account import Account
from eth_utils import to_wei

BALANCE = to_wei(10, "ether")
COLLATERAL_AMOUNT = to_wei(10, "ether")
AMOUNT_TO_MINT = to_wei(100, "ether")
COLLATERAL_TO_COVER = to_wei(20, "ether")


# ------------------------------------------------------------------
#                          SESSION SCOPED
# ------------------------------------------------------------------
@pytest.fixture(scope="session")
def active_network():
    return get_active_network()


@pytest.fixture(scope="session")
def weth(active_network):
    return active_network.manifest_named("weth")


@pytest.fixture(scope="session")
def wbtc(active_network):
    return active_network.manifest_named("wbtc")


@pytest.fixture(scope="session")
def eth_usd(active_network):
    return active_network.manifest_named("eth_usd_price_feed")


@pytest.fixture(scope="session")
def btc_usd(active_network):
    return active_network.manifest_named("btc_usd_price_feed")


@pytest.fixture(scope="session")
def some_user(weth, wbtc):
    entropy = 13
    account = Account.create(entropy)
    boa.env.set_balance(account.address, BALANCE)
    with boa.env.prank(account.address):
        weth.mock_mint() #Mint 100 tokens to the caller.
        wbtc.mock_mint()
    return account.address


@pytest.fixture(scope="session")
def liquidator(weth, wbtc):
    entropy = 234
    account = Account.create(entropy)
    boa.env.set_balance(account.address, BALANCE)
    with boa.env.prank(account.address):
        weth.mock_mint()
        wbtc.mock_mint()
    return account.address

    
# ------------------------------------------------------------------
#                         FUNCTION SCOPED
# ------------------------------------------------------------------
@pytest.fixture(scope="function")
def dsc(active_network):
    return active_network.manifest_named("decentralized_stable_coin")


@pytest.fixture(scope="function")
def dsce(dsc, weth, wbtc, eth_usd, btc_usd):
    return deploy_dsc_engine(dsc)


@pytest.fixture(scope="function")
def dsce_deposited(dsce, some_user, weth):
    with boa.env.prank(some_user):
        weth.approve(dsce.address, COLLATERAL_AMOUNT)
        dsce.deposit_collateral(weth.address, COLLATERAL_AMOUNT)
    return dsce


@pytest.fixture(scope="function")
def dsce_minted(dsce, some_user, weth):
    with boa.env.prank(some_user):
        weth.approve(dsce.address, COLLATERAL_AMOUNT)
        dsce.deposit_and_mint(
            weth.address, COLLATERAL_AMOUNT, AMOUNT_TO_MINT
        )
    return dsce


@pytest.fixture(scope="function")
def starting_liquidator_weth_balance(liquidator, weth):
    return weth.balanceOf(liquidator)

    
@pytest.fixture(scope="function")
def dsce_liquidated(
    starting_liquidator_weth_balance,
    dsce_minted,
    weth,
    dsc,
    some_user,
    liquidator,
    eth_usd,
):
    weth.mock_mint()

    eth_usd_updated_price = 18 * 10**8  
    eth_usd.updateAnswer(eth_usd_updated_price)

    with boa.env.prank(liquidator):
        weth.mock_mint()
        weth.approve(dsce_minted, COLLATERAL_TO_COVER)
        dsce_minted.deposit_and_mint(
            weth, COLLATERAL_TO_COVER, AMOUNT_TO_MINT
        )
        dsc.approve(dsce_minted, AMOUNT_TO_MINT)
        dsce_minted.liquidate(weth, some_user, AMOUNT_TO_MINT)

    return dsce_minted
    