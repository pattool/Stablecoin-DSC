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

## Installation
    - If you have an issue to run it, install virtual environment uv.
    - uv, is an extremely fast Python package and project manager, written in Rust.        
   - ### On macOS and Linux:
        curl -LsSf https://astral.sh/uv/install.sh | sh
       
        - Once install follow the next steps:
           - 1 uv venv
           - 2 uv sync
           - 3 source .venv/bin/activate

   - ### On Windows:
        powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

   - ### Documentation:
        - uv's documentation is available at docs.astral.sh/uv.
        - Additionally, the command line reference documentation can be viewed with uv help.


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


## License

uv is licensed under either of

    - Apache License, Version 2.0, (LICENSE-APACHE or 
      https://www.apache.org/licenses/LICENSE-2.0)
    - MIT license (LICENSE-MIT or https://opensource.org/licenses/MIT)
at your option.

Unless you explicitly state otherwise, any contribution intentionally submitted for inclusion in uv by you, as defined in the Apache-2.0 license, shall be dually licensed as above, without any additional terms or conditions.