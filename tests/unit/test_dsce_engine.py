import boa
import pytest
from eth.codecs.abi.exceptions import EncodeError
from eth_utils import to_wei

from script.mocks.deploy_collateral import deploy_collateral
from contracts import dsc_engine
from contracts.mocks import mock_token
from tests.conftest import COLLATERAL_AMOUNT, AMOUNT_TO_MINT, COLLATERAL_TO_COVER

MIN_HEALTH_FACTOR = to_wei(1, "ether")
LIQUIDATION_THRESHOLD = 50
ZERO = "0x0000000000000000000000000000000000000000"

# ------------------------------------------------------------------
#                       CONSTRUCTOR TESTS
# ------------------------------------------------------------------
def test_reverts_if_token_length_doesnt_match_price_feeds(
    dsc, eth_usd, btc_usd, weth, wbtc
):
    """Test that deployment fails when token and price feed arrays have different lengths"""

    print("\n" + "="*70)
    print("TEST: Reverts if Token Length Doesn't Match Price Feeds")
    print("\n" + "="*70)

    # Setup - intentionally mismatched arrays
    token_addresses = [wbtc, weth, weth]
    price_feed_addresses = [eth_usd, btc_usd]

    print(f"\n📋 Configuration:")
    print(f"   DSC Address: {dsc.address}")

    print(f"\n🪙  Token Addresses (Length: {len(token_addresses)}):")
    for i, token in enumerate(token_addresses):
        print(f"   [{i}] {token.address if hasattr(token, 'address') else token}")

    print(f"\n📊 Price Feed Addresses (Length: {len(price_feed_addresses)}):")
    for i, feed in enumerate(price_feed_addresses):
        print(f"   [{i}] {feed.address if hasattr(feed, 'address') else feed}")

    print(f"\n⚠️  Array Length Mismatch:")
    print(f"   Tokens:      {len(token_addresses)} items")
    print(f"   Price Feeds: {len(price_feed_addresses)} items")
    print(f"   Difference:  {abs(len(token_addresses) - len(price_feed_addresses))} mismatch")
    
    print(f"\n🔴 Expected Behavior:")
    print(f"   Deployment should FAIL with EncodeError")
    print(f"   Reason: Each token needs exactly one price feed")
    
    print(f"\n🧪 Attempting Deployment...")

    # Attempt deployment - should fail
    with pytest.raises(EncodeError):
        dsc_engine.deploy(
            [wbtc.address if hasattr(wbtc, 'address') else wbtc,
             weth.address if hasattr(weth, 'address') else weth,
             weth.address if hasattr(weth, 'address') else weth],
            [eth_usd.address if hasattr(eth_usd, 'address') else eth_usd,
             btc_usd.address if hasattr(btc_usd, 'address') else btc_usd],
            dsc.address
        )
    print(f"   ✅ SUCCESS: Deployment correctly failed with EncodeError")
    print(f"   The contract properly rejected mismatched array lengths")
    
    print("="*70 + "\n")
    
## Short version   
#def test_reverts_if_token_length_doesnt_match_price_feeds(
#    dsc, eth_usd, btc_usd, weth, wbtc
#):
#    """Test that deployment fails when token and price feed arrays have different lengths"""
#
#    try:
#        with pytest.raises(EncodeError):
#            dsc_engine.deploy([wbtc, weth, weth], [eth_usd, btc_usd], dsc.address)
#    
#    except Exception as e:
#        print(f"   ❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")
#        raise


# ------------------------------------------------------------------
#                          PRICE TESTS
# ------------------------------------------------------------------
def test_get_token_amount_from_usd(dsce, weth, eth_usd):
    """Verify that $100 USD converts to 0.05 WETH at the expected ETH/USD price."""
    
    # Debug: Check the price feed
    decimals = eth_usd.decimals()
    price = eth_usd.latestAnswer()
    
    print(f"\n=== Price Feed Debug ===")
    print(f"Decimals: {decimals}")
    print(f"Raw price: {price}")
    print(f"Price in dollars: {price / 10**decimals}")
    
    # Debug: Check USD value calculation
    usd_value_1_eth = dsce.get_usd_value(weth.address, to_wei(1, "ether"))
    print(f"\n=== USD Value Debug ===")
    print(f"USD value of 1 ETH (raw): {usd_value_1_eth}")
    print(f"USD value of 1 ETH (formatted): ${usd_value_1_eth / 10**18}")
    
    # The actual test
    expected_weth = to_wei(0.05, "ether")
    actual_weth = dsce.get_token_amount_from_usd(weth.address, to_wei(100, "ether"))
    
    print(f"\n=== Test Values ===")
    print(f"USD input: $100")
    print(f"Expected WETH (raw): {expected_weth}")
    print(f"Expected WETH (ether): {expected_weth / 10**18}")
    print(f"Actual WETH (raw): {actual_weth}")
    print(f"Actual WETH (ether): {actual_weth / 10**18}")
    print(f"Difference: {actual_weth - expected_weth}")
    print(f"Difference in ether: {(actual_weth - expected_weth) / 10**18}")
    
    assert abs(actual_weth - expected_weth) <= 1
    assert expected_weth == actual_weth

## Short Version
#def test_get_token_amount_from_usd(dsce, weth, eth_usd):
#    """Verify that $100 USD converts to 0.05 WETH at the expected ETH/USD price."""
#    
#    expected_weth = to_wei(0.05, "ether")
#    actual_weth = dsce.get_token_amount_from_usd(weth.address, to_wei(100, "ether"))
#
#    assert abs(actual_weth - expected_weth) <= 1
#    assert expected_weth == actual_weth

    
def test_get_usd_value(dsce, weth):
    """Test that USD value calculation is correct for a given amount of ETH"""

    #Setup
    eth_amount = to_wei(15, "ether")
    expected_usd = to_wei(30_000, "ether")

    print("\n" + "="*70)
    print("TEST: Get USD Value")
    print("="*70)
    
    # Input values
    print(f"\n📊 Input Values:")
    print(f"   ETH Amount (wei): {eth_amount}")
    print(f"   ETH Amount (ether): {eth_amount / 10**18} ETH")
    
    # Expected calculation
    eth_price = 2000  # Assuming $2000/ETH from mock
    print(f"\n💵 Expected Calculation:")
    print(f"   ETH Price: ${eth_price}")
    print(f"   Formula: {eth_amount / 10**18} ETH × ${eth_price} = ${eth_amount / 10**18 * eth_price}")
    print(f"   Expected USD (wei): {expected_usd}")
    print(f"   Expected USD (formatted): ${expected_usd / 10**18:,.2f}")

    # Get actual value from contract
    actual_usd = dsce.get_usd_value(weth, eth_amount)

    print(f"\n✅ Actual Result from Contract:")
    print(f"   Actual USD (raw): {actual_usd}")
    print(f"   Actual USD (formatted): ${actual_usd / 10**18:,.2f}")

    # Comparison
    print(f"\n🔍 Comparison:")
    print(f"   Expected: ${expected_usd / 10**18:,.2f}")
    print(f"   Actual:   ${actual_usd / 10**18:,.2f}")
    print(f"   Match: {'✓ YES' if expected_usd == actual_usd else '✗ NO'}")
                                        
    # Assertion                                
    assert expected_usd == actual_usd, f"USD value mismatch: expected ${expected_usd / 10**18:,.2f}, got ${actual_usd / 10**18:,.2f}"

    print("="*70 + "\n")

    
## Short version
#def test_get_usd_value(dsce, weth):
#    """Test that USD value calculation is correct for a given amount of ETH"""
#
#    #Setup
#    eth_amount = to_wei(15, "ether")
#    expected_usd = to_wei(30_000, "ether")
#
#    # Get actual value from contract
#    actual_usd = dsce.get_usd_value(weth, eth_amount)
#
#    try:
#        if expected_usd != actual_usd:
#            difference = actual_usd - expected_usd
#            print(f"   Difference: {difference} wei (${difference / 10**18:,.2f})")
#
#    except Eception as e:
#        print(f"   ❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")
#        raise
#        
#    # Assertion                                
#    assert expected_usd == actual_usd, f"USD value mismatch: expected ${expected_usd / 10**18:,.2f}, got ${actual_usd / 10**18:,.2f}"

    
# ------------------------------------------------------------------
#                       DEPOSIT COLLATERAL
# ------------------------------------------------------------------
def test_reverts_if_collateral_zero(some_user, weth, dsce):
    """Test that depositing zero collateral reverts"""

    print("\n" + "="*70)
    print("TEST: Reverts if Collateral is Zero")
    print("\n" + "="*70)

    print(f"\n👤 Test Setup:")
    print(f"   User Address: {some_user}")
    print(f"   WETH Address: {weth.address}")
    print(f"   DSCEngine Address: {dsce.address}")

    print(f"\n💰 User Balances Before:")
    user_weth_balance = weth.balanceOf(some_user)
    user_eth_balance = boa.env.get_balance(some_user)
    print(f"   User WETH Balance: {user_weth_balance / 10**18} WETH")
    print(f"   User ETH Balance: {user_eth_balance / 10**18} ETH")

    print(f"\n🔓 Approval Amount:")
    print(f"   Approving: {COLLATERAL_AMOUNT / 10**18} WETH")
    print(f"   Approving (raw): {COLLATERAL_AMOUNT} wei")

    with boa.env.prank(some_user):
        print(f"\n📝 Step 1: Approving WETH spending...")
        weth.approve(dsce.address, COLLATERAL_AMOUNT)    

        # Check allowance after approval
        allowance = weth.allowance(some_user, dsce.address)
        print(f"   ✅ Approval successful")
        print(f"   Allowance set: {allowance / 10**18} WETH")        

        print(f"\n❌ Step 2: Attempting to deposit ZERO collateral...")
        print(f"   Deposit Amount: 0 WETH")
        print(f"   Expected: Should REVERT")
        print(f"   Reason: Contract should reject zero deposits")

        with boa.reverts():
            dsce.deposit_collateral(weth.address, 0)

        print(f"\n✅ SUCCESS: Transaction correctly reverted!")
        print(f"   The contract properly rejected zero collateral")

    print(f"\n💰 User Balances After (should be unchanged):")
    user_weth_balance_after = weth.balanceOf(some_user)
    user_eth_balance_after = boa.env.get_balance(some_user)
    print(f"   User WETH Balance: {user_weth_balance_after / 10**18} WETH")
    print(f"   User ETH Balance: {user_eth_balance_after / 10**18} ETH")
    print(f"   WETH Changed: {(user_weth_balance_after - user_weth_balance) / 10**18} WETH")
    
    print("="*70 + "\n")

## Short version
#def test_reverts_if_collateral_zero(some_user, weth, dsce):
#    """Test that depositing zero collateral reverts"""
#
#    with boa.env.prank(some_user):
#        weth.approve(dsce.address, COLLATERAL_AMOUNT)    
#
#        try:
#            with boa.reverts():
#                dsce.deposit_collateral(weth.address, 0)
#
#        except Exception as e:
#            print(f"   Error Type: {type(e).__name__}")
#            print(f"   Error Message: {str(e)}")
#            raise


def test_reverts_with_unapproved_collateral(some_user, dsce):
    """Test that depositing an unapproved/unsupported token reverts"""

    print("\n" + "="*70)
    print("TEST: Reverts with Unapproved Collateral Token")
    print("="*70)

    print(f"\n🏭 Step 1: Deploying Random Collateral Token...")
    random_collateral = deploy_collateral()

    print(f"   Random Token Deployed at: {random_collateral.address}")
    print(f"   Token Name: {random_collateral.name() if hasattr(random_collateral, 'name') else 'N/A'}")
    print(f"   Token Symbol: {random_collateral.symbol() if hasattr(random_collateral, 'symbol') else 'N/A'}")

    print(f"\n📋 Supported Tokens in DSCEngine:")
    # Try to show supported tokens if available
    print(f"   WETH: Supported ✓")
    print(f"   WBTC: Supported ✓")
    print(f"   Random Token ({random_collateral.address}): NOT Supported ✗")
    
    print(f"\n👤 User Address: {some_user}")
    
    
    with boa.env.prank(some_user):
        print(f"\n💰 Step 2: Minting Random Tokens to User...")
        random_collateral.mock_mint()
        user_balance = random_collateral.balanceOf(some_user)
        print(f"   ✅ Minted successfully")
        print(f"   User Balance: {user_balance / 10**18} tokens")
        print(f"\n📝 Step 3: Approving DSCEngine to spend tokens...")
        print(f"   Approval Amount: {COLLATERAL_AMOUNT / 10**18} tokens")
        print(f"   Spender: {dsce.address}")
        print(f"\n❌ Step 4: Attempting to deposit UNSUPPORTED token...")
        print(f"   Token Address: {random_collateral.address}")
        print(f"   Deposit Amount: {COLLATERAL_AMOUNT / 10**18} tokens")
        print(f"   Expected Result: Should REVERT")
        print(f"   Expected Error: 'DSCEngine: Token not supported'")
        
        with boa.reverts("DSCEngine: Token not supported"):
            # Note: approve is INSIDE the revert context
            # This means if approve fails, the test will fail
            random_collateral.approve(dsce, COLLATERAL_AMOUNT)
            print(f"   ⚠️  Approval executed (inside revert context)")
            
            dsce.deposit_collateral(random_collateral, COLLATERAL_AMOUNT)
            
        print(f"\n✅ SUCCESS: Transaction correctly reverted!")
        print(f"   The DSCEngine properly rejected the unsupported token")
            
    print("="*70 + "\n")
    

## Short version
#def test_reverts_with_unapproved_collateral(some_user, dsce):
#    """Test that depositing an unapproved/unsupported token reverts"""
#
#    random_collateral = deploy_collateral()
#
#    try:
#        with boa.env.prank(some_user):
#            random_collateral.mock_mint()
#            with boa.reverts("DSCEngine: Token not supported"):
#                random_collateral.approve(dsce, COLLATERAL_AMOUNT)                
#                dsce.deposit_collateral(random_collateral, COLLATERAL_AMOUNT)
#
#    except Exception as e:
#        print(f"Actual error: {e}")


def test_can_deposit_collateral_without_minting(dsce_deposited, dsc, some_user, weth):
    """Test that user can deposit collateral without minting any DSC tokens"""
    
    print("\n" + "="*70)
    print("TEST: Can Deposit Collateral Without Minting DSC")
    print("="*70)    
    
    print(f"\n👤 User Information:")
    print(f"   User Address: {some_user}")
    print(f"   DSCEngine Address: {dsce_deposited.address}")
    print(f"   DSC Token Address: {dsc.address}")
    print(f"   WETH Address: {weth.address}")    

    print(f"\n📊 Pre-Deposit State (from fixture):")
    print(f"   ✅ User has already deposited {COLLATERAL_AMOUNT / 10**18} WETH")
    print(f"   (This was done in the 'dsce_deposited' fixture)")

    # Get user's collateral info from DSCEngine
    print(f"\n💰 User's Collateral Information:")
    dsc_minted, collateral_value_usd = dsce_deposited.get_account_information(some_user)
        
    # Get DSC token balance
    dsc_balance = dsc.balanceOf(some_user)

    print(f"\n📊 User's Account State:")
    print(f"   DSC Minted (internal tracking): {dsc_minted / 10**18} DSC")
    print(f"   Collateral Value: ${collateral_value_usd / 10**18:,.2f} USD")
    print(f"   DSC Token Balance: {dsc_balance / 10**18} DSC")
    
    print(f"\n✅ Verification:")
    print(f"   Expected: User has collateral BUT no DSC tokens")
    print(f"   Collateral Value: ${collateral_value_usd / 10**18:,.2f} {'✓' if collateral_value_usd > 0 else '✗'}")
    print(f"   DSC Minted: {dsc_minted / 10**18} DSC {'✓ (0 as expected)' if dsc_minted == 0 else '✗'}")
    print(f"   DSC Balance: {dsc_balance / 10**18} DSC {'✓ (0 as expected)' if dsc_balance == 0 else '✗'}")

    print(f"\n🎯 SUCCESS: User deposited collateral without minting DSC!")
    
    print(f"{'='*70}\n")
    
    assert dsc.balanceOf(some_user) == 0

## Short version
#def test_can_deposit_collateral_without_minting(dsce_deposited, dsc, some_user, weth):
#    """Test that user can deposit collateral without minting any DSC tokens"""
#
#    assert dsc.balanceOf(some_user) == 0

    
def test_can_deposit_collateral_and_get_account_info(dsce_deposited, some_user, weth, eth_usd):
    """Test that we can deposit collateral and retrieve accurate account information"""

    print(f"\n{'='*70}")
    print(f"TEST: Deposit Collateral and Get Account Info")
    print(f"{'='*70}")

    print(f"\n👤 User Information:")
    print(f"   User Address: {some_user}")
    print(f"   WETH Address: {weth.address}")
    print(f"   DSCEngine Address: {dsce_deposited.address}")
    
    print(f"\n💰 Pre-Test Context (from fixture):")
    print(f"   User deposited: {COLLATERAL_AMOUNT / 10**18} WETH")
    print(f"   User deposited (raw): {COLLATERAL_AMOUNT} wei")
    
    # Get ETH price from price feed
    eth_price = eth_usd.latestAnswer()
    print(f"\n📊 Price Feed Information:")
    print(f"   ETH/USD Price (raw): {eth_price}")
    print(f"   ETH/USD Price: ${eth_price / 10**8:,.2f}")
    print(f"   Price Feed Decimals: 8")
    
    # Calculate expected USD value
    expected_usd = (COLLATERAL_AMOUNT * eth_price * 10**10) // 10**18
    print(f"\n💵 Expected Collateral Value:")
    print(f"   Formula: {COLLATERAL_AMOUNT / 10**18} WETH × ${eth_price / 10**8:,.2f}")
    print(f"   Expected USD Value: ${expected_usd / 10**18:,.2f}")

    print(f"\n🔍 Step 1: Get Account Information from Contract")
    dsc_minted, collateral_value_usd = dsce_deposited.get_account_information(some_user)
    
    print(f"   ✓ DSC Minted (internal): {dsc_minted / 10**18} DSC")
    print(f"   ✓ Collateral Value USD: ${collateral_value_usd / 10**18:,.2f}")
    
    print(f"\n✅ Assertion 1: Check DSC Minted is Zero")
    print(f"   Expected: 0 DSC")
    print(f"   Actual: {dsc_minted / 10**18} DSC")
    print(f"   Status: {'✓ PASS' if dsc_minted == 0 else '✗ FAIL'}")
    assert dsc_minted == 0, f"Expected 0 DSC minted, got {dsc_minted / 10**18} DSC"

    print(f"\n✅ Assertion 2: Check Collateral Value is Positive")
    print(f"   Expected: > $0")
    print(f"   Actual: ${collateral_value_usd / 10**18:,.2f}")
    print(f"   Status: {'✓ PASS' if collateral_value_usd > 0 else '✗ FAIL'}")
    assert collateral_value_usd > 0, "Collateral value should be positive"
    
    print(f"\n🔄 Step 2: Convert USD Value Back to Token Amount")
    print(f"   Converting ${collateral_value_usd / 10**18:,.2f} USD back to WETH...")

    expected_deposit_amount = dsce_deposited.get_token_amount_from_usd(
        weth.address, collateral_value_usd
    )
    
    print(f"   Result: {expected_deposit_amount / 10**18} WETH")
    print(f"   Result (raw): {expected_deposit_amount} wei")
    
    print(f"\n✅ Assertion 3: Roundtrip Conversion Check")
    print(f"   Original Deposit: {COLLATERAL_AMOUNT / 10**18} WETH")
    print(f"   After USD Conversion: {expected_deposit_amount / 10**18} WETH")
    print(f"   Difference: {abs(expected_deposit_amount - COLLATERAL_AMOUNT)} wei")
    print(f"   Difference (ether): {abs(expected_deposit_amount - COLLATERAL_AMOUNT) / 10**18}")
    
    print(f"   Status: ✓ PERFECT MATCH")
    
    print(f"\n🎯 Test Summary:")
    print(f"   ✓ User has 0 DSC minted (can deposit without minting)")
    print(f"   ✓ Collateral value is tracked correctly (${collateral_value_usd / 10**18:,.2f})")
    print(f"   ✓ USD ↔ Token conversion is accurate")
    
    print(f"{'='*70}\n")
    
    assert expected_deposit_amount == COLLATERAL_AMOUNT, \
        f"Conversion mismatch: expected {COLLATERAL_AMOUNT / 10**18} WETH, got {expected_deposit_amount / 10**18} WETH"

## Short version    
#def test_can_deposit_collateral_and_get_account_info(dsce_deposited, some_user, weth, eth_usd):
#    """Test that we can deposit collateral and retrieve accurate account information"""
#    
#    # Get account info
#    dsc_minted, collateral_value_usd = dsce_deposited.get_account_information(some_user)
#    
#    # Check DSC minted is 0
#    assert dsc_minted == 0
#    
#    # Check collateral value is positive (deposited something)
#    assert collateral_value_usd > 0
#
#    expected_deposit_amount = dsce_deposited.get_token_amount_from_usd(
#        weth, collateral_value_usd
#    )
#    assert expected_deposit_amount == COLLATERAL_AMOUNT
    

# ------------------------------------------------------------------
#               DEPOSIT COLLATERAL AND MINT DSC TESTS
# ------------------------------------------------------------------
def test_reverts_if_minted_dsc_breaks_health_factor(dsce, weth, eth_usd, some_user):
    """Test that minting too much DSC relative to collateral reverts due to broken health factor"""

    print(f"\n{'='*70}")
    print(f"TEST: Reverts if Minted DSC Breaks Health Factor")
    print(f"{'='*70}")
    
    print(f"\n👤 User Information:")
    print(f"   User Address: {some_user}")
    print(f"   WETH Address: {weth.address}")
    print(f"   DSCEngine Address: {dsce.address}")
    
    # Get price data
    round_data = eth_usd.latestRoundData()
    price = round_data[1]

    print(f"\n📊 Price Feed Data:")
    print(f"   Round ID: {round_data[0]}")
    print(f"   ETH/USD Price (raw): {price}")
    print(f"   ETH/USD Price: ${price / 10**8:,.2f}")
    print(f"   Timestamp: {round_data[2]}")
    
    # Get constants
    additional_fee_precision = dsce.ADDITIONAL_FEE_PRECISION()
    precision = dsce.PRECISION()
    liquidation_threshold = dsce.LIQUIDATION_TRESHOLD()
    liquidation_precision = dsce.LIQUIDATION_PRECISION()
    min_health_factor = dsce.MIN_HEALTH_FACTOR()

    print(f"\n🔧 Contract Constants:")
    print(f"   ADDITIONAL_FEE_PRECISION: {additional_fee_precision}")
    print(f"   PRECISION: {precision}")
    print(f"   LIQUIDATION_THRESHOLD: {liquidation_threshold}%")
    print(f"   LIQUIDATION_PRECISION: {liquidation_precision}")
    print(f"   MIN_HEALTH_FACTOR: {min_health_factor / 10**18}")
    
    print(f"\n💰 Collateral Information:")
    print(f"   Collateral Amount: {COLLATERAL_AMOUNT / 10**18} WETH")
    print(f"   Collateral Amount (raw): {COLLATERAL_AMOUNT} wei")

    # Calculate collateral value in USD
    collateral_usd_value = dsce.get_usd_value(weth.address, COLLATERAL_AMOUNT)
    print(f"   Collateral USD Value: ${collateral_usd_value / 10**18:,.2f}")
    
    # Calculate amount to mint (intentionally breaks health factor)
    amount_to_mint = (
        COLLATERAL_AMOUNT * (price * dsce.ADDITIONAL_FEE_PRECISION())
) // dsce.PRECISION()

    print(f"\n🪙 DSC Minting Calculation:")
    print(f"   Formula: (collateral × price × fee_precision) / precision")
    print(f"   Amount to Mint: {amount_to_mint / 10**18:,.2f} DSC")
    print(f"   Amount to Mint (raw): {amount_to_mint} wei")
    
    # Calculate what the health factor would be
    print(f"\n🏥 Health Factor Analysis:")
    print(f"   This mints DSC equal to 100% of collateral value")
    print(f"   Required: At least 200% collateralization (50% threshold)")

    # Calculate expected health factor
    collateral_adjusted = (collateral_usd_value * liquidation_threshold) // liquidation_precision
    expected_health_factor = (collateral_adjusted * precision) // amount_to_mint if amount_to_mint > 0 else 0

    print(f"   Collateral Adjusted for Threshold: ${collateral_adjusted / 10**18:,.2f}")
    print(f"   Expected Health Factor: {expected_health_factor / 10**18:.4f}")
    print(f"   Minimum Health Factor: {min_health_factor / 10**18:.4f}")
    print(f"   Status: {'✗ UNHEALTHY' if expected_health_factor < min_health_factor else '✓ HEALTHY'}")
    
    print(f"   ⚠️  This SHOULD revert - health factor too low!")
        
    
    with boa.env.prank(some_user):
        print(f"\n📝 Step 1: Approving WETH...")
        weth.approve(dsce.address, COLLATERAL_AMOUNT)
        print(f"   ✓ Approved {COLLATERAL_AMOUNT / 10**18} WETH")
        
        print(f"\n🧮 Step 2: Calculate Health Factor...")
        calculated_health_factor = dsce.calculate_health_factor(
            amount_to_mint, collateral_usd_value
        )
        print(f"   Calculated Health Factor: {calculated_health_factor / 10**18:.4f}")
        print(f"   Min Required: {min_health_factor / 10**18:.4f}")
        print(f"   Healthy? {'✓ YES' if calculated_health_factor >= min_health_factor else '✗ NO'}")
        
        print(f"\n❌ Step 3: Attempting to Deposit and Mint (should revert)...")
        print(f"   Depositing: {COLLATERAL_AMOUNT / 10**18} WETH")
        print(f"   Minting: {amount_to_mint / 10**18:,.2f} DSC")
        print(f"   Expected: Revert with 'DSCEngine: Health factor broken'")
        
        with boa.reverts("DSCEngine: Health factor broken"):
            dsce.deposit_and_mint(weth.address, COLLATERAL_AMOUNT, amount_to_mint)
        
        print(f"\n✅ SUCCESS: Transaction correctly reverted!")
        print(f"   The contract properly rejected the unhealthy position")
    
    print(f"\n🎯 Test Summary:")
    print(f"   ✓ Attempted to mint 100% of collateral value as DSC")
    print(f"   ✓ Health factor would be {expected_health_factor / 10**18:.4f} (below minimum 1.0)")
    print(f"   ✓ Contract correctly rejected the unhealthy position")
    
    print(f"{'='*70}\n")

## Short version
#def test_reverts_if_minted_dsc_breaks_health_factor(dsce, weth, eth_usd, some_user):
#    """Test that minting too much DSC relative to collateral reverts due to broken health factor""" 
#
#    # Get constants
#    additional_fee_precision = dsce.ADDITIONAL_FEE_PRECISION()
#    precision = dsce.PRECISION()
#    price = eth_usd.latestRoundData()[1]
#    collateral_usd_value = dsce.get_usd_value(weth.address, COLLATERAL_AMOUNT) 
#    
#    amount_to_mint = (
#        COLLATERAL_AMOUNT * (price * additional_fee_precision)
#    ) // precision
#
#    try:
#        with boa.env.prank(some_user):
#            weth.approve(dsce, COLLATERAL_AMOUNT)
#            dsce.calculate_health_factor(
#                amount_to_mint, collateral_usd_value
#            )
#            with boa.reverts("DSCEngine: Health factor broken"):
#                dsce.deposit_and_mint(
#                    weth.address, COLLATERAL_AMOUNT, amount_to_mint
#                ) 
#
#    except Exception as e:
#        print(f"   Error Type: {type(e).__name__}")


def test_can_mint_with_deposited_collateral(dsce_minted, dsc, some_user, weth, eth_usd):
    """Test that user can mint DSC after depositing sufficient collateral"""
    
    print(f"\n{'='*70}")
    print(f"TEST: Can Mint DSC with Deposited Collateral")
    print(f"{'='*70}")
    
    print(f"\n👤 User Information:")
    print(f"   User Address: {some_user}")
    print(f"   DSCEngine Address: {dsce_minted.address}")
    print(f"   DSC Token Address: {dsc.address}")
    print(f"   WETH Address: {weth.address}")
    
    print(f"\n📋 Pre-Test Context (from fixture):")
    print(f"   The 'dsce_minted' fixture should have:")
    print(f"   1. Deposited collateral")
    print(f"   2. Minted DSC tokens")

    # Get contract constants
    min_health_factor = dsce_minted.MIN_HEALTH_FACTOR()
    liquidation_threshold = dsce_minted.LIQUIDATION_TRESHOLD()
    liquidation_precision = dsce_minted.LIQUIDATION_PRECISION()

    print(f"\n🔧 Contract Constants:")
    print(f"   MIN_HEALTH_FACTOR: {min_health_factor / 10**18:.2f}")
    print(f"   LIQUIDATION_THRESHOLD: {liquidation_threshold}%")
    print(f"   LIQUIDATION_PRECISION: {liquidation_precision}")
    
    # Get price information
    eth_price = eth_usd.latestAnswer()
    print(f"\n📊 Price Feed:")
    print(f"   ETH/USD Price: ${eth_price / 10**8:,.2f}")

    # Get user's account information
    print(f"\n💰 User's Account State:")
    total_dsc_minted, collateral_value_usd = dsce_minted.get_account_information(some_user)
    
    print(f"   Total DSC Minted (internal): {total_dsc_minted / 10**18:,.2f} DSC")
    print(f"   Collateral Value: ${collateral_value_usd / 10**18:,.2f} USD")

    # Calculate health factor
    health_factor = dsce_minted.health_factor(some_user)
    print(f"\n🏥 Health Factor:")
    print(f"   Current Health Factor: {health_factor / 10**18:.4f}")
    print(f"   Minimum Required: {min_health_factor / 10**18:.4f}")
    print(f"   Status: {'✓ HEALTHY' if health_factor >= min_health_factor else '✗ UNHEALTHY'}")
    
    # Calculate collateralization ratio
    collateral_ratio = (collateral_value_usd * 100) // total_dsc_minted
    print(f"   Collateralization Ratio: {collateral_ratio / 10**18:.2f}%")

    
    # Get actual DSC token balance
    print(f"\n🪙 DSC Token Balance Check:")
    user_balance = dsc.balanceOf(some_user)
    print(f"   User DSC Balance (raw): {user_balance}")
    print(f"   User DSC Balance: {user_balance / 10**18:,.2f} DSC")
    
    print(f"\n📝 Expected Values:")
    print(f"   Expected to Mint (from constant): {AMOUNT_TO_MINT / 10**18:,.2f} DSC")
    print(f"   Expected to Mint (raw): {AMOUNT_TO_MINT}")
    
    print(f"\n✅ Verification:")
    print(f"   Expected Balance: {AMOUNT_TO_MINT / 10**18:,.2f} DSC")
    print(f"   Actual Balance: {user_balance / 10**18:,.2f} DSC")
    print(f"   Match: {'✓ YES' if user_balance == AMOUNT_TO_MINT else '✗ NO'}")

    
    print(f"\n🎯 Test Validations:")
    print(f"   ✓ User successfully minted {AMOUNT_TO_MINT / 10**18:,.2f} DSC")
    print(f"   ✓ DSC tokens were transferred to user's wallet")
    print(f"   ✓ Internal tracking matches actual token balance")
    print(f"   ✓ Health factor remains healthy ({health_factor / 10**18:.4f})")
    
    # Additional context
    print(f"\n📊 Summary:")
    print(f"   Collateral Value: ${collateral_value_usd / 10**18:,.2f}")
    print(f"   DSC Minted: {total_dsc_minted / 10**18:,.2f} DSC")
    print(f"   DSC Token Balance: {user_balance / 10**18:,.2f} DSC")
    print(f"   Health Factor: {health_factor / 10**18:.4f}")

    overcollateralization = ((collateral_value_usd - total_dsc_minted) / total_dsc_minted) * 100
    print(f"   Overcollateralization: {overcollateralization / 10**18:.2f}%")
    
    print(f"{'='*70}\n")
    
    assert user_balance == AMOUNT_TO_MINT, \
        f"DSC balance mismatch: expected {AMOUNT_TO_MINT / 10**18} DSC, got {user_balance / 10**18} DSC"

# Short version
#def test_can_mint_with_deposited_collateral(dsce_minted, dsc, some_user, weth, eth_usd):
#    """Test that user can mint DSC after depositing sufficient collateral"""
#
#    # Get actual DSC token balance
#    user_balance = dsc.balanceOf(some_user)
#
#    assert user_balance == AMOUNT_TO_MINT

    
# ------------------------------------------------------------------
#                          MINT DSC TESTS
# ------------------------------------------------------------------
def test_reverts_if_mint_amount_breaks_health_factor(
    dsce_deposited, eth_usd, some_user, weth
):
    """Test that minting too much DSC breaks health factor and reverts"""

    print(f"\n{'='*70}")
    print(f"TEST: Reverts if Mint Amount Breaks Health Factor")
    print(f"{'='*70}")

    # Get price and calculate amount to mint (100% of collateral)
    price = eth_usd.latestRoundData()[1]
    amount_to_mint = (
        COLLATERAL_AMOUNT * (price * dsce_deposited.ADDITIONAL_FEE_PRECISION())
    ) // dsce_deposited.PRECISION()

    collateral_usd = dsce_deposited.get_usd_value(weth.address, COLLATERAL_AMOUNT)
    
    print(f"\n📊 Setup:")
    print(f"   ETH Price: ${price / 10**8:,.2f}")
    print(f"   Collateral: {COLLATERAL_AMOUNT / 10**18} WETH (${collateral_usd / 10**18:,.2f})")
    print(f"   Trying to Mint: {amount_to_mint / 10**18:,.2f} DSC (100% of collateral)")

    # Calculate health factor
    health_factor = dsce_deposited.calculate_health_factor(amount_to_mint, collateral_usd)
    min_hf = dsce_deposited.MIN_HEALTH_FACTOR()
    
    print(f"\n🏥 Health Factor:")
    print(f"   Would Be: {health_factor / 10**18:.4f}")
    print(f"   Minimum: {min_hf / 10**18:.4f}")
    print(f"   Status: {'✗ UNHEALTHY' if health_factor < min_hf else '✓ HEALTHY'} - Should REVERT")
    
    with boa.env.prank(some_user):
        print(f"\n❌ Attempting to mint {amount_to_mint / 10**18:,.2f} DSC...")
        
        with boa.reverts("DSCEngine: Health factor broken"):
            dsce_deposited.mint_dsc(amount_to_mint)

        print(f"✅ SUCCESS: Correctly reverted with health factor error")

    print(f"\n🎯 Validation: Contract prevents unhealthy minting")
    print(f"{'='*70}\n")

## Short version
#def test_reverts_if_mint_amount_breaks_health_factor(
#    dsce_deposited, eth_usd, some_user, weth
#):
#    """Test that minting too much DSC breaks health factor and reverts"""
#
#    # Get price and calculate amount to mint (100% of collateral)
#    price = eth_usd.latestRoundData()[1]
#    amount_to_mint = (
#        COLLATERAL_AMOUNT * (price * dsce_deposited.ADDITIONAL_FEE_PRECISION())
#    ) // dsce_deposited.PRECISION()
#
#    collateral_usd = dsce_deposited.get_usd_value(weth.address, COLLATERAL_AMOUNT)
#
#    try:
#        with boa.env.prank(some_user):
#            dsce_deposited.calculate_health_factor(amount_to_mint, collateral_usd)
#            with boa.reverts("DSCEngine: Health factor broken"):
#                dsce_deposited.mint_dsc(amount_to_mint)
#            
#    except Exception as e:
#        print(f"Actual error: {e}")

                
def test_can_mint_dsc(dsce_deposited, dsc, some_user, weth):
    """Test that user can mint DSC with deposited collateral"""

    print(f"\n{'='*70}")
    print(f"TEST: Can Mint DSC")
    print(f"{'='*70}")

    # Get initial state
    total_dsc_minted_before, collateral_value = dsce_deposited.get_account_information(some_user)
    balance_before = dsc.balanceOf(some_user)
    health_factor_before = dsce_deposited.health_factor(some_user)
    
    print(f"\n📊 Before Minting:")
    print(f"   Collateral Value: ${collateral_value / 10**18:,.2f}")
    print(f"   DSC Balance: {balance_before / 10**18} DSC")
    print(f"   Health Factor: {health_factor_before / 10**18:.4f}")
    
    print(f"\n🪙 Minting {AMOUNT_TO_MINT / 10**18} DSC...")

    with boa.env.prank(some_user):
        dsce_deposited.mint_dsc(AMOUNT_TO_MINT)
        user_balance = dsc.balanceOf(some_user)
        
        # Get updated state
        total_dsc_minted_after, _ = dsce_deposited.get_account_information(some_user)
        health_factor_after = dsce_deposited.health_factor(some_user)        
        
        print(f"\n📊 After Minting:")
        print(f"   DSC Balance: {user_balance / 10**18} DSC")
        print(f"   Total DSC Minted: {total_dsc_minted_after / 10**18} DSC")
        print(f"   Health Factor: {health_factor_after / 10**18:.4f}")
        
        print(f"\n✅ Verification:")
        print(f"   Expected: {AMOUNT_TO_MINT / 10**18} DSC")
        print(f"   Actual: {user_balance / 10**18} DSC")
        print(f"   Match: {'✓ YES' if user_balance == AMOUNT_TO_MINT else '✗ NO'}")        
                
        assert user_balance == AMOUNT_TO_MINT

        print(f"\n🎯 SUCCESS: Minted {AMOUNT_TO_MINT / 10**18} DSC (HF: {health_factor_after / 10**18:.4f})")        
    print(f"{'='*70}\n")

## Short version
#def test_can_mint_dsc(dsce_deposited, dsc, some_user, weth):
#    """Test that user can mint DSC with deposited collateral"""
#
#    try:
#        with boa.env.prank(some_user):
#            dsce_deposited.mint_dsc(AMOUNT_TO_MINT)
#            user_balance = dsc.balanceOf(some_user)
#            
#    except Exception as e:
#        print(f"Actual error: {e}")
#        
#    assert user_balance == AMOUNT_TO_MINT

   
# ------------------------------------------------------------------
#                          BURN DSC TESTS
# ------------------------------------------------------------------
def test_cant_burn_more_than_user_has(dsce, dsc, some_user):
    """Test that burning more DSC than user has minted reverts"""

    print(f"\n{'='*70}")
    print(f"TEST: Can't Burn More Than User Has")
    print(f"{'='*70}")

    # Get initial state
    total_dsc_minted, collateral_value = dsce.get_account_information(some_user)
    dsc_balance = dsc.balanceOf(some_user)

    print(f"\n📊 User State:")
    print(f"   DSC Balance: {dsc_balance / 10**18} DSC")
    print(f"   DSC Minted (internal): {total_dsc_minted / 10**18} DSC")
    print(f"   Collateral Value: ${collateral_value / 10**18:,.2f}")
    
    print(f"\n❌ Attempting to burn 1 wei DSC (user has {dsc_balance} wei)...")

    
    
    with boa.env.prank(some_user):
        print(f"   Approving DSCEngine to burn 1 wei...")
        dsc.approve(dsce.address, 1)
        
        print(f"   Trying to burn 1 wei DSC...")
        print(f"   Expected: Should REVERT (user has 0 DSC minted)") 
        
        with boa.reverts():
            dsce.burn_dsc(1)

        print(f"   ✅ Correctly reverted!")

    print(f"\n🎯 Validation: Cannot burn DSC that wasn't minted")
    print(f"{'='*70}\n")

## Short version
#def test_cant_burn_more_than_user_has(dsce, dsc, some_user):
#    """Test that burning more DSC than user has minted reverts"""
#
#    with boa.env.prank(some_user):
#        dsc.approve(dsce.address, 1)
#
#        try:
#            with boa.reverts():
#                dsce.burn_dsc(1)
#
#        except Exception as e:
#            print(f"Actual error: {e}")

            
def test_can_burn_dsc(dsce_minted, dsc, some_user):
    """Test that user can burn their minted DSC tokens"""
    
    print(f"\n{'='*70}")
    print(f"TEST: Can Burn DSC")
    print(f"{'='*70}")

    # Get initial state
    total_dsc_minted_before, collateral_value = dsce_minted.get_account_information(some_user)
    balance_before = dsc.balanceOf(some_user)
    health_factor_before = dsce_minted.health_factor(some_user)

    print(f"\n📊 Before Burning:")
    print(f"   DSC Balance: {balance_before / 10**18} DSC")
    print(f"   DSC Minted (internal): {total_dsc_minted_before / 10**18} DSC")
    print(f"   Collateral Value: ${collateral_value / 10**18:,.2f}")
    print(f"   Health Factor: {health_factor_before / 10**18:.4f}")
    
    print(f"\n🔥 Burning {AMOUNT_TO_MINT / 10**18} DSC...")
    
    with boa.env.prank(some_user):
        dsc.approve(dsce_minted, AMOUNT_TO_MINT)
        print(f"   ✓ Approved DSCEngine to burn tokens")
                
        dsce_minted.burn_dsc(AMOUNT_TO_MINT)
        user_balance = dsc.balanceOf(some_user)
        
        # Get updated state
        total_dsc_minted_after, _ = dsce_minted.get_account_information(some_user)
        health_factor_after = dsce_minted.health_factor(some_user)        

        print(f"\n📊 After Burning:")
        print(f"   DSC Balance: {user_balance / 10**18} DSC")
        print(f"   DSC Minted (internal): {total_dsc_minted_after / 10**18} DSC")
        print(f"   Health Factor: {health_factor_after / 10**18:.4f}")
        
        print(f"\n✅ Verification:")
        print(f"   Expected: 0 DSC")
        print(f"   Actual: {user_balance / 10**18} DSC")
        print(f"   Match: {'✓ YES' if user_balance == 0 else '✗ NO'}")
        
        assert user_balance == 0

        print(f"\n🎯 SUCCESS: Burned all DSC (HF improved to {health_factor_after / 10**18:.4f})")
    
    print(f"{'='*70}\n")

## Short version
#def test_can_burn_dsc(dsce_minted, dsc, some_user):
#    """Test that user can burn their minted DSC tokens"""
#
#    try:
#        with boa.env.prank(some_user):
#            dsc.approve(dsce_minted, AMOUNT_TO_MINT)
#            dsce_minted.burn_dsc(AMOUNT_TO_MINT)
#            user_balance = dsc.balanceOf(some_user)
#
#    except Exception as e:
#        print(f"Actual error: {e}")
#        
#    assert user_balance == 0


# ------------------------------------------------------------------
#                     REDEEM COLLATERAL TESTS
# ------------------------------------------------------------------
def test_can_redeem_collateral(dsce, weth, dsc, some_user):
    """Test that user can redeem collateral by burning DSC"""
    
    print(f"\n{'='*70}")
    print(f"TEST: Can Redeem Collateral")
    print(f"{'='*70}")
    
    with boa.env.prank(some_user):
        # Initial state
        weth_balance_start = weth.balanceOf(some_user)
        dsc_balance_start = dsc.balanceOf(some_user)
        
        print(f"\n📊 Initial State:")
        print(f"   WETH Balance: {weth_balance_start / 10**18} WETH")
        print(f"   DSC Balance: {dsc_balance_start / 10**18} DSC")
        
        # Deposit and mint
        print(f"\n💰 Step 1: Deposit {COLLATERAL_AMOUNT / 10**18} WETH & Mint {AMOUNT_TO_MINT / 10**18} DSC...")
        
        weth.approve(dsce, COLLATERAL_AMOUNT)
        dsc.approve(dsce, AMOUNT_TO_MINT)
        dsce.deposit_and_mint(weth.address, COLLATERAL_AMOUNT, AMOUNT_TO_MINT)
        
        # After deposit/mint        
        total_dsc_minted, collateral_value = dsce.get_account_information(some_user)
        weth_balance_mid = weth.balanceOf(some_user)
        dsc_balance_mid = dsc.balanceOf(some_user)
        
        print(f"\n📊 After Deposit & Mint:")
        print(f"   WETH Balance: {weth_balance_mid / 10**18} WETH")
        print(f"   DSC Balance: {dsc_balance_mid / 10**18} DSC")
        print(f"   Collateral Value: ${collateral_value / 10**18:,.2f}")        

        # Redeem collateral
        print(f"\n🔄 Step 2: Redeem {COLLATERAL_AMOUNT / 10**18} WETH by burning {AMOUNT_TO_MINT / 10**18} DSC...")    
        dsce.redeem_for_dsc(weth, COLLATERAL_AMOUNT, AMOUNT_TO_MINT)
        
        # Final state
        weth_balance_end = weth.balanceOf(some_user)
        user_balance = dsc.balanceOf(some_user)
        total_dsc_after, collateral_after = dsce.get_account_information(some_user)
        
        print(f"\n📊 After Redeem:")
        print(f"   WETH Balance: {weth_balance_end / 10**18} WETH (returned to original)")
        print(f"   DSC Balance: {user_balance / 10**18} DSC")
        print(f"   DSC Minted (internal): {total_dsc_after / 10**18} DSC")
        print(f"   Collateral Value: ${collateral_after / 10**18:,.2f}")
        
        print(f"\n✅ Verification:")
        print(f"   Expected DSC Balance: 0")
        print(f"   Actual DSC Balance: {user_balance / 10**18}")
        print(f"   Match: {'✓ YES' if user_balance == 0 else '✗ NO'}")

        assert user_balance == 0

        print(f"\n🎯 SUCCESS: Full cycle complete (deposit → mint → redeem → burn)")
    
    print(f"{'='*70}\n")

##Short version
#def test_can_redeem_collateral(dsce, weth, dsc, some_user):
#    """Test that user can redeem collateral by burning DSC"""
#    try:
#        with boa.env.prank(some_user):
#            weth.approve(dsce, COLLATERAL_AMOUNT)
#            dsc.approve(dsce, AMOUNT_TO_MINT)
#            
#            dsce.deposit_and_mint(weth.address, COLLATERAL_AMOUNT, AMOUNT_TO_MINT)
#            dsce.redeem_for_dsc(weth, COLLATERAL_AMOUNT, AMOUNT_TO_MINT)
#        
#            user_balance = dsc.balanceOf(some_user)
#
#    except Exception as e:
#        print(f"Actual error: {e}")
#        
#    assert user_balance == 0

    
def test_properly_reports_health_factor(dsce_minted, some_user):
    """Test that health factor is calculated and reported correctly"""

    print(f"\n{'='*70}")
    print(f"TEST: Properly Reports Health Factor")
    print(f"{'='*70}")
    
    # Get account information
    total_dsc_minted, collateral_value_usd = dsce_minted.get_account_information(some_user)
    
    # Get constants
    liquidation_threshold = dsce_minted.LIQUIDATION_TRESHOLD()
    liquidation_precision = dsce_minted.LIQUIDATION_PRECISION()
    
    print(f"\n📊 User's Account:")
    print(f"   Collateral Value: ${collateral_value_usd / 10**18:,.2f}")
    print(f"   DSC Minted: {total_dsc_minted / 10**18:,.2f} DSC")
    print(f"   Liquidation Threshold: {liquidation_threshold}%")


    # Manual calculation
    collateral_adjusted = (collateral_value_usd * liquidation_threshold) // liquidation_precision
    expected_health_factor = to_wei(100, "ether")

    print(f"\n🧮 Health Factor Calculation:")
    print(f"   Collateral Adjusted: ${collateral_adjusted / 10**18:,.2f}")
    print(f"   Formula: (collateral × threshold / precision) / DSC minted")
    print(f"   Expected HF: {expected_health_factor / 10**18:.4f}")
    
    # Get actual health factor    
    actual_health_factor = dsce_minted.health_factor(some_user)

    print(f"\n✅ Verification:")
    print(f"   Expected: {expected_health_factor / 10**18:.4f}")
    print(f"   Actual: {actual_health_factor / 10**18:.4f}")
    print(f"   Match: {'✓ YES' if expected_health_factor == actual_health_factor else '✗ NO'}")
    
    assert expected_health_factor == actual_health_factor

    print(f"\n🎯 SUCCESS: Health factor = {actual_health_factor / 10**18:.4f} (200x overcollateralized)")
    print(f"{'='*70}\n")

## Short version
#def test_properly_reports_health_factor(dsce_minted, some_user):
#    """Test that health factor is calculated and reported correctly"""
#
#    expected_health_factor = to_wei(100, "ether")
#    actual_health_factor = dsce_minted.health_factor(some_user)
#    assert expected_health_factor == actual_health_factor

    
def test_health_factor_can_go_below_one(dsce_minted, eth_usd, some_user):
    """Test that health factor goes below 1 when collateral value drops"""
    
    print(f"\n{'='*70}")
    print(f"TEST: Health Factor Can Go Below One")
    print(f"{'='*70}")
    
    # Initial state
    total_dsc_minted, collateral_value_before = dsce_minted.get_account_information(some_user)
    health_factor_before = dsce_minted.health_factor(some_user)
    eth_price_before = eth_usd.latestAnswer()
    
    print(f"\n📊 Initial State:")
    print(f"   ETH Price: ${eth_price_before / 10**8:,.2f}")
    print(f"   Collateral Value: ${collateral_value_before / 10**18:,.2f}")
    print(f"   DSC Minted: {total_dsc_minted / 10**18:,.2f} DSC")
    print(f"   Health Factor: {health_factor_before / 10**18:.4f}")

    # Update price (crash ETH from $2000 to $18)
    eth_usd_updated_price = 18 * 10**8
    print(f"\n💥 Crashing ETH Price: ${eth_price_before / 10**8:,.2f} → ${eth_usd_updated_price / 10**8:,.2f}")
    eth_usd.updateAnswer(eth_usd_updated_price)

    # After price update
    _, collateral_value_after = dsce_minted.get_account_information(some_user)
    user_health_factor = dsce_minted.health_factor(some_user)
    
    print(f"\n📊 After Price Crash:")
    print(f"   ETH Price: ${eth_usd_updated_price / 10**8:,.2f} (99% drop!)")
    print(f"   Collateral Value: ${collateral_value_after / 10**18:,.2f}")
    print(f"   DSC Minted: {total_dsc_minted / 10**18:,.2f} DSC (unchanged)")
    print(f"   Health Factor: {user_health_factor / 10**18:.4f}")

    print(f"\n✅ Verification:")
    expected_hf = to_wei(0.9, "ether")
    print(f"   Expected: {expected_hf / 10**18:.4f}")
    print(f"   Actual: {user_health_factor / 10**18:.4f}")
    print(f"   Match: {'✓ YES' if user_health_factor == expected_hf else '✗ NO'}")
    print(f"   Status: {'❌ LIQUIDATABLE (HF < 1.0)' if user_health_factor < 10**18 else '✓ SAFE'}")    
    
    assert user_health_factor == to_wei(0.9, "ether")

    print(f"\n🎯 SUCCESS: HF dropped to {user_health_factor / 10**18:.4f} - position is now liquidatable")
    print(f"{'='*70}\n")

## Short version
#def test_health_factor_can_go_below_one(dsce_minted, eth_usd, some_user):
#    """Test that health factor goes below 1 when collateral value drops"""
#    
#    eth_usd_updated_price = 18 * 10**8
#    eth_usd.updateAnswer(eth_usd_updated_price)
#    user_health_factor = dsce_minted.health_factor(some_user)
#    assert user_health_factor == to_wei(0.9, "ether")

    
# ------------------------------------------------------------------
#                     LIQUIDATION TESTS
# ------------------------------------------------------------------
def test_cant_liquidate_good_health_factor(
    dsce_minted, weth, dsc, some_user, liquidator
):
    """Test that liquidation fails when user has healthy position"""
    
    print(f"\n{'='*70}")
    print(f"TEST: Can't Liquidate Good Health Factor")
    print(f"{'='*70}")
    
    # Check user's health factor
    user_hf = dsce_minted.health_factor(some_user)
    total_dsc_minted, collateral_value = dsce_minted.get_account_information(some_user)
    min_hf = dsce_minted.MIN_HEALTH_FACTOR()
    
    print(f"\n👤 User (Target) State:")
    print(f"   Address: {some_user}")
    print(f"   Collateral Value: ${collateral_value / 10**18:,.2f}")
    print(f"   DSC Minted: {total_dsc_minted / 10**18:,.2f} DSC")
    print(f"   Health Factor: {user_hf / 10**18:.4f}")
    print(f"   Status: {'✓ HEALTHY' if user_hf >= min_hf else '❌ LIQUIDATABLE'}")

    # Setup liquidator
    print(f"\n🦈 Liquidator Setup:")
    print(f"   Address: {liquidator}")
    weth.mint(liquidator, COLLATERAL_TO_COVER)
    print(f"   Minted {COLLATERAL_TO_COVER / 10**18} WETH")
    
    with boa.env.prank(liquidator):
        weth.approve(dsce_minted, COLLATERAL_TO_COVER)
        dsce_minted.deposit_and_mint(
            weth.address, COLLATERAL_TO_COVER, AMOUNT_TO_MINT
        )
        liquidator_dsc = dsc.balanceOf(liquidator)
        print(f"   Deposited {COLLATERAL_TO_COVER / 10**18} WETH")
        print(f"   Minted {liquidator_dsc / 10**18:,.2f} DSC")        
                
        dsc.approve(dsce_minted, AMOUNT_TO_MINT)
        print(f"   Approved DSC for liquidation")

        print(f"\n❌ Attempting to liquidate healthy position...")
        print(f"   Target: {some_user}")
        print(f"   Target HF: {user_hf / 10**18:.4f} (> {min_hf / 10**18:.4f})")
        print(f"   Debt to Cover: {AMOUNT_TO_MINT / 10**18:,.2f} DSC")
        print(f"   Expected: Should REVERT (user is healthy)")
        
        with boa.reverts("DSCEngine: Health factor is good"):
            dsce_minted.liquidate(weth.address, some_user, AMOUNT_TO_MINT)

        print(f"   ✅ Correctly reverted!")
    
    print(f"\n🎯 SUCCESS: Cannot liquidate healthy positions (HF = {user_hf / 10**18:.4f})")
    print(f"{'='*70}\n")

## Short version
#def test_cant_liquidate_good_health_factor(
#    dsce_minted, weth, dsc, some_user, liquidator
#):
#    """Test that liquidation fails when user has healthy position"""
#
#    weth.mint(liquidator, COLLATERAL_TO_COVER)
#    
#    try:
#        with boa.env.prank(liquidator):
#            weth.approve(dsce_minted, COLLATERAL_TO_COVER)
#            dsce_minted.deposit_and_mint(
#                weth.address, COLLATERAL_TO_COVER, AMOUNT_TO_MINT
#            )
#            liquidator_dsc = dsc.balanceOf(liquidator)
#            dsc.approve(dsce_minted, AMOUNT_TO_MINT)
#            
#            
#            with boa.reverts("DSCEngine: Health factor is good"):
#                dsce_minted.liquidate(weth.address, some_user, AMOUNT_TO_MINT)
#        
#    except Exception as e:
#        print(f"Actual error: {e}")

        
def test_liquidation_payout_is_correct(
    starting_liquidator_weth_balance, dsce_liquidated, weth, liquidator
):
    """Test that liquidator receives correct collateral amount including bonus"""
    
    print(f"\n{'='*70}")
    print(f"TEST: Liquidation Payout is Correct")
    print(f"{'='*70}")

    # Get liquidator's balance
    liquidator_weth_balance = weth.balanceOf(liquidator)
    weth_gained = liquidator_weth_balance - starting_liquidator_weth_balance
    
    print(f"\n💰 Liquidator Balances:")
    print(f"   Starting WETH: {starting_liquidator_weth_balance / 10**18:.18f} WETH")
    print(f"   Current WETH: {liquidator_weth_balance / 10**18:.18f} WETH")
    print(f"   WETH Gained: {weth_gained / 10**18:.18f} WETH")

    # Calculate expected payout
    liquidation_bonus = dsce_liquidated.LIQUIDATION_BONUS()
    debt_covered_in_weth = dsce_liquidated.get_token_amount_from_usd(weth.address, AMOUNT_TO_MINT)
    bonus_weth = debt_covered_in_weth // liquidation_bonus
    expected_weth = debt_covered_in_weth + bonus_weth
    
    print(f"\n🧮 Payout Calculation:")
    print(f"   Debt Covered: {AMOUNT_TO_MINT / 10**18:,.2f} DSC")
    print(f"   Debt in WETH: {debt_covered_in_weth / 10**18:.18f} WETH")
    print(f"   Liquidation Bonus: {liquidation_bonus}%")
    print(f"   Bonus WETH: {bonus_weth / 10**18:.18f} WETH")
    print(f"   Total Expected: {expected_weth / 10**18:.18f} WETH")

    hard_coded_expected = 6_111_111_111_111_111_110

    print(f"\n✅ Verification:")
    print(f"   Expected (calculated): {expected_weth / 10**18:.18f} WETH")
    print(f"   Expected (hard-coded): {hard_coded_expected / 10**18:.18f} WETH")
    print(f"   Actual: {liquidator_weth_balance / 10**18:.18f} WETH")
    print(f"   Hard-coded match: {'✓ YES' if liquidator_weth_balance == hard_coded_expected else '✗ NO'}")
    print(f"   Calculated match: {'✓ YES' if liquidator_weth_balance == expected_weth else '✗ NO'}")
    
    assert liquidator_weth_balance == hard_coded_expected
    assert liquidator_weth_balance == expected_weth

    bonus_percentage = (bonus_weth / debt_covered_in_weth) * 100
    print(f"\n🎯 SUCCESS: Liquidator received {weth_gained / 10**18:.18f} WETH ({bonus_percentage:.1f}% bonus)")
    print(f"{'='*70}\n")

## Short version
#def test_liquidation_payout_is_correct(
#    starting_liquidator_weth_balance, dsce_liquidated, weth, liquidator
#):
#    """Test that liquidator receives correct collateral amount including bonus"""
#
#    # Get liquidator's balance
#    liquidator_weth_balance = weth.balanceOf(liquidator)
#
#    # Calculate expected payout
#    liquidation_bonus = dsce_liquidated.LIQUIDATION_BONUS()
#    debt_covered_in_weth = dsce_liquidated.get_token_amount_from_usd(weth.address, AMOUNT_TO_MINT)
#    bonus_weth = debt_covered_in_weth // liquidation_bonus
#    expected_weth = debt_covered_in_weth + bonus_weth
#
#    hard_coded_expected = 6_111_111_111_111_111_110
#    
#    assert liquidator_weth_balance == hard_coded_expected
#    assert liquidator_weth_balance == expected_weth

    
def test_cant_redeem_if_breaks_health_factor(dsce_minted, weth, some_user):
    """Test that redemption fails if it would break health factor"""
    
    print(f"\n{'='*70}")
    print(f"TEST: Can't Redeem if Breaks Health Factor")
    print(f"{'='*70}")
    
    # User has minted DSC, so redeeming all collateral would break health factor
    total_dsc_minted, collateral_value = dsce_minted.get_account_information(some_user)
    health_factor_before = dsce_minted.health_factor(some_user)
    min_hf = dsce_minted.MIN_HEALTH_FACTOR()
    
    print(f"\n📊 User State:")
    print(f"   Collateral Value: ${collateral_value / 10**18:,.2f}")
    print(f"   DSC Minted: {total_dsc_minted / 10**18:,.2f} DSC")
    print(f"   Health Factor: {health_factor_before / 10**18:.4f}")
    
    print(f"\n❌ Attempting to redeem ALL collateral...")
    print(f"   Redeeming: {COLLATERAL_AMOUNT / 10**18} WETH")
    print(f"   Would leave: $0 collateral with {total_dsc_minted / 10**18:,.2f} DSC debt")
    print(f"   Expected: Should REVERT (would break health factor)")
    
    with boa.env.prank(some_user):
        with boa.reverts("DSCEngine: Health factor broken"):
            dsce_minted.redeem_collateral(weth.address, COLLATERAL_AMOUNT)
        
        print(f"   ✅ Correctly reverted!")
    
    print(f"\n🎯 SUCCESS: Cannot redeem collateral that breaks health factor")
    print(f"{'='*70}\n")

## Short version
#def test_cant_redeem_if_breaks_health_factor(dsce_minted, weth, some_user):
#    """Test that redemption fails if it would break health factor"""
#
#    # User has minted DSC, so redeeming all collateral would break health factor
#    total_dsc_minted, collateral_value = dsce_minted.get_account_information(some_user)
#    health_factor_before = dsce_minted.health_factor(some_user)
#    dsce_minted.MIN_HEALTH_FACTOR()
#
#    with boa.env.prank(some_user):
#        with boa.reverts("DSCEngine: Health factor broken"):
#            dsce_minted.redeem_collateral(weth.address, COLLATERAL_AMOUNT)


# ------------------------------------------------------------------
#                          PAUSE TESTS
# ------------------------------------------------------------------
def test_owner_can_pause(dsce):
    """Verify that the owner can successfully pause the contract."""
    with boa.env.prank(dsce.owner()):
        dsce.pause()
    assert dsce.paused() == True

    
def test_owner_can_unpause(paused_dsce):
    """Verify that the owner can successfully unpause the contract."""
    with boa.env.prank(paused_dsce.owner()):
        paused_dsce.unpause()
    assert paused_dsce.paused() == False


def test_non_owner_cannot_pause(dsce, user):
    """Verify that a non-owner address cannot pause the contract."""
    with boa.env.prank(user):
        with boa.reverts():
            dsce.pause()

            
def test_non_owner_cannot_unpause(paused_dsce, user):
    """Verify that a non-owner address cannot unpause the contract."""
    with boa.env.prank(user):
        with boa.reverts():
            paused_dsce.unpause()

            
def test_deposit_reverts_when_paused(paused_dsce, weth, user):
    """Verify that deposit_collateral reverts when the contract is paused."""
    with boa.env.prank(user):
        with boa.reverts("DSCEngine: Contract is paused"):
            paused_dsce.deposit_collateral(weth.address, to_wei(1, "ether"))


def test_mint_reverts_when_paused(paused_dsce, user):
    """Verify that mint_dsc reverts when the contract is paused."""
    with boa.env.prank(user):
        with boa.reverts("DSCEngine: Contract is paused"):
            paused_dsce.mint_dsc(to_wei(100, "ether"))

            
def test_liquidate_reverts_when_paused(paused_dsce, weth, user):
    """Verify that liquidate reverts when the contract is paused."""
    with boa.env.prank(user):
        with boa.reverts("DSCEngine: Contract is paused"):
            paused_dsce.liquidate(weth.address, user, to_wei(100, "ether"))

            
def test_cannot_pause_twice(dsce):
    """Verify that pausing an already paused contract reverts."""
    with boa.env.prank(dsce.owner()):
        dsce.pause()
        with boa.reverts():
            dsce.pause()

            
def test_cannot_unpause_if_not_paused(dsce):
    """Verify that unpausing an already active contract reverts."""
    with boa.env.prank(dsce.owner()):
        with boa.reverts():
            dsce.unpause()

            
def test_deposit_and_mint_reverts_when_paused(paused_dsce, weth, user):
    """Verify that deposit_and_mint reverts when the contract is paused,
    ensuring both deposit and mint operations are blocked in a single call."""
    with boa.env.prank(user):
        with boa.reverts("DSCEngine: Contract is paused"):
            paused_dsce.deposit_and_mint(weth.address, to_wei(1, "ether"), to_wei(100, "ether"))


def test_redeem_collateral_reverts_when_paused(paused_dsce, weth, user):
    """Verify that redeem_collateral reverts when the contract is paused."""
    with boa.env.prank(user):
        with boa.reverts("DSCEngine: Contract is paused"):
            paused_dsce.redeem_collateral(weth.address, to_wei(1, "ether"))


def test_redeem_collateral_for_dsc_reverts_when_paused(paused_dsce, weth, user):
    """Verify that redeem_collateral_for_dsc reverts when the contract is paused."""
    with boa.env.prank(user):
        with boa.reverts("DSCEngine: Contract is paused"):
            paused_dsce.redeem_for_dsc(weth.address, to_wei(1, "ether"), to_wei(100, "ether"))


def test_burn_dsc_reverts_when_paused(paused_dsce, user):
    """Verify that burn_dsc reverts when the contract is paused."""
    with boa.env.prank(user):
        with boa.reverts("DSCEngine: Contract is paused"):
            paused_dsce.burn_dsc(to_wei(100, "ether"))


# ------------------------------------------------------------------
#                     PRICE FEED STALENESS TESTS
# ------------------------------------------------------------------
def test_reverts_when_price_feed_is_stale(dsce, weth, eth_usd):
    """Verify that get_usd_value reverts when the price feed is older than 1 hour."""
    
    # Advance time by 2 hours — makes the price stale
    boa.env.time_travel(seconds=7200)
    
    with boa.reverts("DSCEngine: Stale price feed"):
        dsce.get_usd_value(weth.address, to_wei(1, "ether"))


def test_reverts_when_price_is_invalid(dsce, weth, eth_usd):
    """Verify that get_usd_value reverts when the price feed returns zero."""
    
    # Set price to 0 — simulates a broken/invalid price feed
    eth_usd.updateAnswer(0)
    
    with boa.reverts("DSCEngine: Invalid price"):
        dsce.get_usd_value(weth.address, to_wei(1, "ether"))


def test_fresh_price_feed_works(dsce, weth, eth_usd):
    """Verify that get_usd_value works normally with a fresh valid price."""
    
    expected_usd = to_wei(2000, "ether")
    actual_usd = dsce.get_usd_value(weth.address, to_wei(1, "ether"))
    
    assert actual_usd == expected_usd


def test_get_collateral_balance_of_user(dsce_deposited, some_user, weth):
    """Verify get_collateral_balance_of_user returns correct deposited amount."""
    balance = dsce_deposited.get_collateral_balance_of_user(some_user, weth.address)
    assert balance == COLLATERAL_AMOUNT


def test_get_token_amount_from_usd_reverts_when_stale(dsce, weth):
    """Verify get_token_amount_from_usd reverts when price feed is stale."""
    boa.env.time_travel(seconds=7200)
    with boa.reverts("DSCEngine: Stale price feed"):
        dsce.get_token_amount_from_usd(weth.address, to_wei(100, "ether"))


def test_get_token_amount_from_usd_reverts_when_price_invalid(dsce, weth, eth_usd):
    """Verify get_token_amount_from_usd reverts when price is zero."""
    eth_usd.updateAnswer(0)
    with boa.reverts("DSCEngine: Invalid price"):
        dsce.get_token_amount_from_usd(weth.address, to_wei(100, "ether"))


def test_health_factor_is_max_when_no_dsc_minted(dsce_deposited, some_user):
    """Verify health factor returns max uint256 when user has no DSC minted."""
    health_factor = dsce_deposited.health_factor(some_user)
    assert health_factor == 2**256 - 1


# ------------------------------------------------------------------
#                 TWO-STEP OWNERSHIP TRANSFER TESTS
# ------------------------------------------------------------------
def test_owner_can_initiate_transfer(dsce):
    """Verify that the owner can initiate an ownership transfer
    by setting a pending_owner without transferring ownership yet."""
    new_owner = boa.env.generate_address()
    with boa.env.prank(dsce.owner()):
        dsce.transfer_ownership(new_owner)
    assert dsce.pending_owner() == new_owner


def test_pending_owner_can_accept(dsce):
    """Verify that the pending owner can complete the ownership transfer
    by calling accept_ownership, updating owner and clearing pending_owner."""
    new_owner = boa.env.generate_address()
    with boa.env.prank(dsce.owner()):
        dsce.transfer_ownership(new_owner)
    with boa.env.prank(new_owner):
        dsce.accept_ownership()
    assert dsce.owner() == new_owner
    assert dsce.pending_owner() == ZERO


def test_non_pending_owner_cannot_accept(dsce):
    """Verify that a random address cannot accept ownership,
    preventing unauthorized takeover of the contract."""
    new_owner = boa.env.generate_address()
    random_user = boa.env.generate_address()
    with boa.env.prank(dsce.owner()):
        dsce.transfer_ownership(new_owner)
    with boa.env.prank(random_user):
        with boa.reverts("DSCEngine: Not pending owner"):
            dsce.accept_ownership()


def test_non_owner_cannot_initiate_transfer(dsce, user):
    """Verify that a non-owner cannot initiate an ownership transfer,
    ensuring only the current owner can propose a new owner."""
    new_owner = boa.env.generate_address()
    with boa.env.prank(user):
        with boa.reverts("DSCEngine: Not owner"):
            dsce.transfer_ownership(new_owner)


def test_cannot_transfer_to_zero_address(dsce):
    """Verify that transferring ownership to the zero address reverts,
    preventing accidental permanent loss of contract ownership."""
    with boa.env.prank(dsce.owner()):
        with boa.reverts("DSCEngine: Invalid address"):
            dsce.transfer_ownership(ZERO)


def test_transfer_resets_pending_owner(dsce):
    """Verify that after ownership is accepted, pending_owner is reset
    to the zero address, preventing any replay of the transfer."""
    new_owner = boa.env.generate_address()
    with boa.env.prank(dsce.owner()):
        dsce.transfer_ownership(new_owner)
    with boa.env.prank(new_owner):
        dsce.accept_ownership()
    assert dsce.pending_owner() == ZERO