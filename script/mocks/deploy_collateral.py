from contracts.mocks import mock_token



def deploy_collateral():
    print("Deploying token...")
    return mock_token.deploy()


def moccasin_main():
    return deploy_collateral()