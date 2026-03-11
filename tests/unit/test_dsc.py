import boa

ZERO = "0x0000000000000000000000000000000000000000"


def test_cannot_mint_to_zero_address(dsc):
    """Verify that minting to the zero address reverts,
    preventing tokens from being permanently burned on mint."""
    
    with boa.env.prank(dsc.owner()):
        with boa.reverts():
            dsc.mint(ZERO, 0)


def test_cant_burn_more_than_you_have(dsc):
    """Verify that burning more tokens than the owner holds reverts,
    preventing underflow and unauthorized supply reduction."""
    
    with boa.env.prank(dsc.owner()):
        with boa.reverts():
            dsc.burn_from(dsc.owner(), 1)