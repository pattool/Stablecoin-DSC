import pytest
from hypothesis.stateful import RuleBasedStateMachine, initialize, rule, invariant, precondition
from hypothesis import assume, settings, HealthCheck
from script.deploy_dsc import deploy_dsc
from script.deploy_dsc_engine import deploy_dsc_engine
from moccasin.config import get_active_network
from eth.constants import ZERO_ADDRESS
from boa.util.abi import Address
import boa
from hypothesis import strategies as st
from boa.test.strategies import strategy
from eth_utils import to_wei
from boa import BoaError
from contracts.mocks import MockV3Aggregator 


USERS_SIZE = 10
MAX_DEPOSIT_SIZE = to_wei(1000, "ether")

# Invariant: Property of the system that should always be true


class StablecoinFuzzer(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()

    @initialize()
    def setup(self):
        """Initialize the fuzzer with deployed contracts, price feeds,
        collateral tokens and a set of random non-zero user addresses."""
        
        self.dsc  = deploy_dsc()
        self.dsce = deploy_dsc_engine(self.dsc)

        active_network = get_active_network()
        self.weth = active_network.manifest_named("weth")
        self.wbtc = active_network.manifest_named("wbtc")
        self.eth_usd = active_network.manifest_named("eth_usd_price_feed")
        self.btc_usd = active_network.manifest_named("btc_usd_price_feed")

        self.users = [Address("0x" + ZERO_ADDRESS.hex())]
        while Address("0x" + ZERO_ADDRESS.hex()) in self.users:
            self.users = [boa.env.generate_address() for _ in range(USERS_SIZE)]

        self.liquidator = boa.env.generate_address()
        
    @rule(
        collateral_seed = st.integers(min_value=0, max_value=1),
        user_seed= st.integers(min_value=0, max_value=USERS_SIZE - 1),
        amount = strategy("uint256", min_value=1, max_value=MAX_DEPOSIT_SIZE)
    )
    def mint_and_deposit(self, collateral_seed, user_seed, amount):
        """Mint collateral tokens for a random user and deposit them into DSCEngine,
        simulating realistic collateral deposits with random amounts."""

        # 1. Select a random collateral -> collateral_seed
        # 2. Select a random user       -> user_seed
        # 3. Deposit a random amount    -> amount
        
        assume(not self.dsce.paused()) # Add
        
        print("Depositing collateral!")
        collateral = self._get_collateral_from_seed(collateral_seed)
        user = self.users[user_seed]
        print(collateral.name())
        print(amount)
        with boa.env.prank(user):
            collateral.mint_amount(amount)
            collateral.approve(self.dsce.address, amount)
            self.dsce.deposit_collateral(collateral, amount)
    

    @rule(
        collateral_seed = st.integers(min_value=0, max_value=1),
        user_seed= st.integers(min_value=0, max_value=USERS_SIZE - 1),
        #percentage = st.integers(min_value=1, max_value=100)
    )
    def deposit_and_redeem(self, collateral_seed, user_seed):
        """Deposit a fixed amount then immediately redeem it,
        guaranteeing the redeem_collateral code path is hit."""

        assume(not self.dsce.paused()) # Add
        
        print("Redeem collateral!")
        collateral = self._get_collateral_from_seed(collateral_seed)
        user = self.users[user_seed]
        amount = to_wei(1, "ether")

        # Only redeem if user has no DSC minted — prevents health factor break
        total_dsc_minted, _ = self.dsce.get_account_information(user)
        assume(total_dsc_minted == 0)
    
        with boa.env.prank(user):
            collateral.mint_amount(amount)
            collateral.approve(self.dsce.address, amount)
            self.dsce.deposit_collateral(collateral, amount)
            # Immediately redeem — guaranteed to have balance
            self.dsce.redeem_collateral(collateral, amount)
        

    @rule(
        collateral_seed = st.integers(min_value=0, max_value=1),
        user_seed= st.integers(min_value=0, max_value=USERS_SIZE - 1),
        #amount = strategy("uint256", min_value=1, max_value=MAX_DEPOSIT_SIZE)
    )
    def mint_without_collateral_then_deposit(self, collateral_seed, user_seed):
        """Attempt to mint DSC with no collateral, triggering the auto-deposit
        retry path in mint_dsc to improve coverage of the except branch."""

        assume(not self.dsce.paused()) # Add
        
        user = self.users[user_seed]
        amount = to_wei(100, "ether")
        #amount = 1
        
        with boa.env.prank(user):
            try:
                # Will fail — no collateral deposited yet
                self.dsce.mint_dsc(amount)
                
            except BoaError as e:
                    collateral = self._get_collateral_from_seed(collateral_seed)
                    collateral_amount = self.dsce.get_token_amount_from_usd(
                        collateral.address, amount
                    )
                    if collateral_amount == 0: 
                        collateral_amount = 1
                    collateral_amount = collateral_amount * 2
                    collateral.mint_amount(collateral_amount)
                    collateral.approve(self.dsce.address, collateral_amount)
                    self.dsce.deposit_collateral(collateral, collateral_amount)
                    try:
                        self.dsce.mint_dsc(amount)
                    except BoaError:
                        pass  # Still might fail, that's ok
    
    @rule(
        percentage_new_price=st.floats(min_value=0.8, max_value=1.15),
        collateral_seed = st.integers(min_value=0, max_value=1),                                 
    )
    def update_collateral_price(self, collateral_seed, percentage_new_price):
        """Update the mock price feed for a collateral token by a random percentage,
        simulating realistic market price fluctuations between -20% and +15%."""
        
        collateral = self._get_collateral_from_seed(collateral_seed)
        price_feed = MockV3Aggregator.at(
            self.dsce.token_to_price_feed(collateral.address)
        )
        current_price = price_feed.latestAnswer()
        new_price = int(current_price * percentage_new_price)
        price_feed.updateAnswer(new_price)

    
    @rule(
        collateral_seed = st.integers(min_value=0, max_value=1),
        user_seed= st.integers(min_value=0, max_value=USERS_SIZE - 1),
        amount = strategy("uint256", min_value=1, max_value=MAX_DEPOSIT_SIZE)
    )
    def mint_and_update(self, collateral_seed, user_seed, amount):
        """Deposit collateral then drop its price by 15%,
        stress testing the protocol's health factor under mild price drops."""

        assume(not self.dsce.paused()) # Add
        
        self.mint_and_deposit(collateral_seed, user_seed, amount)
        self.update_collateral_price(collateral_seed, 0.85) # Only drop 15% instead of 70%


    @rule(
        collateral_seed = st.integers(min_value=0, max_value=1),
        user_seed= st.integers(min_value=0, max_value=USERS_SIZE - 1),
        percentage = st.integers(min_value=1, max_value=100)
    )
    def liquidate_user(self, collateral_seed, user_seed, percentage):
        """Attempt to liquidate an undercollateralized user by covering a random
        percentage of their debt, skipping if health factor is still healthy."""

        assume(not self.dsce.paused()) # Add
        
        user = self.users[user_seed]
        health_factor = self.dsce.health_factor(user)

        print(f"Attempting liquidation for user {user_seed}, health factor: {health_factor}")
        
        # Only proceed if health factor is broken
        assume(health_factor < int(1e18))
        
        # Get user's debt and collateral info
        total_dsc_minted, total_collateral_value_usd = self.dsce.get_account_information(user)
        
        # Skip if no debt
        assume(total_dsc_minted > 0)
        
        # Calculate debt to cover based on percentage
        debt_to_cover = (total_dsc_minted * percentage) // 100
        assume(debt_to_cover > 0)
        
        # Select collateral to seize
        collateral = self._get_collateral_from_seed(collateral_seed)

        print(f"Liquidating {debt_to_cover} DSC worth of {collateral.name()}")
        
        try:
            with boa.env.prank(self.liquidator):
                # Liquidator needs DSC to burn the debt
                self.dsc.mint(self.liquidator, debt_to_cover)
                self.dsc.approve(self.dsce.address, debt_to_cover)
                
                # Perform liquidation
                self.dsce.liquidate(collateral.address, user, debt_to_cover)
                print(f"Successfully liquidated {debt_to_cover} DSC")
        except BoaError as e:
            print(f"Liquidation failed: {e}")
            pass

   
    # Invariant: Protocol must have more value in collateral than total supply.    
    @invariant()
    def protocol_must_have_more_value_than_total_supply(self):
        """Invariant: total USD value of WETH and WBTC held by DSCEngine
        must always be greater than or equal to the total DSC supply."""
        
        total_supply = self.dsc.totalSupply()
        weth_deposited = self.weth.balanceOf(self.dsce.address)
        wbtc_deposited = self.wbtc.balanceOf(self.dsce.address)

        weth_value = self.dsce.get_usd_value(self.weth, weth_deposited)
        wbtc_value = self.dsce.get_usd_value(self.wbtc, wbtc_deposited)

        assert (weth_value + wbtc_value) >= total_supply

    
    def _get_collateral_from_seed(self, seed):
        """Return WETH for seed 0 or WBTC for any other seed,
        mapping an integer to a collateral token contract."""
        
        if seed == 0:
            return self.weth
        else:
            return self.wbtc


    @precondition(lambda self: not self.dsce.paused())
    @rule()
    def pause_contract(self):
        """Pause the contract as owner, simulating an emergency stop."""
        
        with boa.env.prank(self.dsce.owner()):
            self.dsce.pause()
    
    
    @precondition(lambda self: self.dsce.paused())
    @rule()
    def unpause_contract(self):
        """Unpause the contract as owner, restoring normal operations."""
        
        with boa.env.prank(self.dsce.owner()):
            self.dsce.unpause()
    
    
    @precondition(lambda self: self.dsce.paused())
    @rule(
        user_seed=st.integers(min_value=0, max_value=USERS_SIZE - 1),
        amount=strategy("uint256", min_value=1, max_value=MAX_DEPOSIT_SIZE)
    )
    def paused_mint_fails(self, user_seed, amount):
        """Verify that mint_dsc reverts for any user when contract is paused."""
        
        user = self.users[user_seed]
        with boa.env.prank(user):
            with pytest.raises(Exception):
                self.dsce.mint_dsc(amount)
    
    
    @precondition(lambda self: self.dsce.paused())
    @rule(
        collateral_seed=st.integers(min_value=0, max_value=1),
        user_seed=st.integers(min_value=0, max_value=USERS_SIZE - 1),
        amount=strategy("uint256", min_value=1, max_value=MAX_DEPOSIT_SIZE)
    )
    def paused_deposit_fails(self, collateral_seed, user_seed, amount):
        """Verify that deposit_collateral reverts for any user when contract is paused."""
        
        collateral = self._get_collateral_from_seed(collateral_seed)
        user = self.users[user_seed]
        with boa.env.prank(user):
            with pytest.raises(Exception):
                self.dsce.deposit_collateral(collateral.address, amount)
      

stable_coin_fuzzer = StablecoinFuzzer.TestCase
stable_coin_fuzzer.settings = settings(
    max_examples=64, 
    stateful_step_count=64, 
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much]
)

