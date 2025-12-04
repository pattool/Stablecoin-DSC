# Moccasin Project

🐍 Welcome to the Decentralized Stablecoin (DSC) project!

## What we want to do:
1. Users can deposit $200 of ETH.
   
2. They can then mint $50 of Stablecoin.
   1. This means they will have a 4/1 ratio of collateral to stablecoin (200 / 50 = 4 -> ratio 4/1)
   2. We will set a required collateral ratio of 2/1
    
3. If the price of ETH drops, for example to $50, others
   should be able to liquidate those users!

## Smart Contract Components Needed:

1. Deposit function - Lock collateral
2. Mint function - Issue stablecoin (if collateral ratio > 200%)
3. Health check - Calculate current collateral ratio
4. Liquidation function - Allow others to liquidate unhealthy positions
5. Price oracle - Get current ETH price (critical!)

## Quickstart

1. Deploy to a fake local network that titanoboa automatically spins up!

```bash
mox run deploy
```

2. Run tests

```
mox test

mox test -s (with print statements)
```

_For documentation, please run `mox --help` or visit [the Moccasin documentation](https://cyfrin.github.io/moccasin)_
