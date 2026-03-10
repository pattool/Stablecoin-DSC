from contracts.mocks import mock_token



def deploy_collateral():
    """Deploy a mock ERC20 token 
    to simulate collateral for testing purposes."""
    
    print("Deploying token...")
    return mock_token.deploy()


def moccasin_main():
    """Entry point: deploy a mock collateral 
    token on the active network."""
    
    return deploy_collateral()