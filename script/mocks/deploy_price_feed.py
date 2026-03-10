from contracts.mocks import MockV3Aggregator

DECIMALS = 8
INITIAL_VALUE = 200_000_000_000  # $2,000


def deploy_price_feed():
    """Deploy a mock Chainlink V3 price feed
    with 8 decimals and an initial price of $2,000."""
    
    return MockV3Aggregator.deploy(DECIMALS, INITIAL_VALUE)


def moccasin_main():
    """Entry point: deploy the mock
    ETH/USD price feed on the active network."""
    
    return deploy_price_feed()