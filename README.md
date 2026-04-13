# Decentralized Stablecoin (DSC) — Vyper / Moccasin

A decentralized, algorithmic stablecoin protocol built in **Vyper 0.4.1** using the **Moccasin** framework.  
Inspired by MakerDAO/DAI. Extended and hardened with additional security features beyond the original course material from Cyfrin Updraft.

---

## Overview

Users deposit crypto collateral (WETH or WBTC) to mint DSC, a USD-pegged stablecoin.  
The protocol enforces a minimum 200% collateralization ratio. Undercollateralized positions can be liquidated by anyone.

- **Collateral:** Exogenous (WETH, WBTC)
- **Stability Mechanism:** Algorithmic / Decentralized
- **Peg:** USD (via Chainlink price feeds)

---

## How It Works

1. Deposit WETH or WBTC as collateral
2. Mint DSC up to 50% of your collateral value (200% collateralization ratio)
3. If your health factor drops below 1.0, your position becomes liquidatable
4. Liquidators repay your debt and receive your collateral plus a bonus

---

## Smart Contracts

| Contract | Description |
|---|---|
| `decentralized_stable_coin.vy` | ERC20 DSC token using Snekmate libraries |
| `dsc_engine.vy` | Core protocol engine: deposits, minting, liquidations, security |

---

## Security Features

- **Emergency Pause** — Owner can halt all state-changing operations instantly
- **Chainlink Staleness Check** — Rejects price data older than 1 hour
- **Invalid Price Check** — Rejects zero or negative price feed responses
- **Two-Step Ownership Transfer** — Prevents accidental loss of contract ownership; new owner must explicitly accept
- **Health Factor Enforcement** — Every mint and redemption checks collateralization ratio

---

## Protocol Features

- **Dynamic Liquidation Bonus** — Bonus scales with risk:
  - Health Factor ≥ 0.8 → **10% bonus**
  - Health Factor ≥ 0.5 → **15% bonus**
  - Health Factor < 0.5 → **20% bonus**
- **Deposit & Mint in one transaction** — Gas efficient combined operation
- **Redeem & Burn in one transaction** — Full exit in a single call

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Vyper 0.4.1 | Smart contract language |
| Moccasin (mox) | Vyper framework (deployment, testing) |
| Titanoboa | EVM interpreter for Python-native testing |
| Chainlink | On-chain price feeds (ETH/USD, BTC/USD) |
| Snekmate | Audited Vyper libraries (ERC20, Ownable) |
| Hypothesis | Property-based fuzz testing |

---

## Test Suite

- **Unit tests** — Full coverage of all contract functions and edge cases
- **Fuzz tests** — Stateful property-based testing with Hypothesis
- **Coverage** — 97% on `dsc_engine.vy`

Key fuzz invariant tested:  
> *The total USD value of collateral held by the protocol must always be ≥ the total DSC supply.*

---

## Planned Features

- **Minting Fee** — Small protocol fee on DSC minting
- **Support for More Collateral Tokens** — Extend beyond 2 tokens using dynamic arrays
- **Interest Rate on Minted DSC** — Continuous debt accumulation (similar to MakerDAO stability fee)

---

## Installation

```bash
git clone https://github.com/pattool/Stablecoin-DSC
cd mox-stablecoin-cu
mox install
```

If you need a virtual environment:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv
uv sync
source .venv/bin/activate
```

```powershell
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## Quickstart

```bash
# Deploy locally
mox run deploy

# Compile
mox compile

# Run tests
mox test

# Run tests with print output
mox test -s

# Run a specific test
mox test -k test_name -s
```

---

## License

This project is licensed under either of

- Apache License, Version 2.0 ([LICENSE-APACHE](https://www.apache.org/licenses/LICENSE-2.0))
- MIT license ([LICENSE-MIT](https://opensource.org/licenses/MIT))

at your option.