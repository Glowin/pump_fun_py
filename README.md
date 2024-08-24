# pump_fun_py

Decided to share my pump.fun codebase with the world because: 

1.) There are too many scammers out there on github and telegram.

2.) The IDL for pump.fun isn't public information, but it should be. 

Clone the repo, and add your Public Key (wallet), Private Key and RPC to the Config.py.

Check out https://github.com/bilix-software/solana-pump-fun for a typescript version. 

### Swap Layout
Do not change the hard-coded values as they are part of the actual swap instructions for the pump.fun program. 

**buy = 16927863322537952870**

**sell = 12502976635542562355**

To see for yourself, decode the "Instruction Raw Data" from any pump fun transaction using the find_instruction.py. 

### Contact

Contact me if you need help integrating the code into your own project. 

Telegram: Allen_A_Taylor (AL The Bot Father)

### FAQS

**What format should my private key be in?** 

The private key should be in the base58 string format, not bytes. 

**Why are my transactions being dropped?** 

You get what you pay for. If you use the public RPC, you're going to get rekt. Spend the money for Helius or Quick Node. Also, play around with the compute limits and lamports.

**What format is slippage in?** 

Slippage is in decimal format. Example: .05 slippage is 5%. 

### Example

```
from pump_fun import buy

#PUMP FUN MINT ADDRESS (NOT RAYDIUM)
mint_str = "token_to_buy"

#BUY
buy(mint_str=mint_str, sol_in=.1, slippage_decimal=.25)

```
```
from pump_fun import sell
from utils import get_token_balance

#PUMP FUN MINT ADDRESS (NOT RAYDIUM)
mint_str = "token_to_sell"

#SELL
token_balance = get_token_balance()
sell(mint_str=mint_str, token_balance=token_balance, slippage_decimal=.25)

```

# init database

``` sql
CREATE TABLE juejin_data_engine (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mint VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    symbol VARCHAR(255),
    description TEXT,
    image_uri VARCHAR(255),
    metadata_uri VARCHAR(255),
    twitter VARCHAR(255),
    telegram VARCHAR(255),
    bonding_curve VARCHAR(255),
    associated_bonding_curve VARCHAR(255),
    creator VARCHAR(255),
    created_timestamp BIGINT,
    raydium_pool VARCHAR(255),
    complete BOOLEAN,
    virtual_sol_reserves BIGINT,
    virtual_token_reserves BIGINT,
    hidden BOOLEAN,
    total_supply BIGINT,
    website VARCHAR(255),
    show_name BOOLEAN,
    last_trade_timestamp BIGINT,
    king_of_the_hill_timestamp BIGINT,
    market_cap FLOAT,
    reply_count INT,
    last_reply VARCHAR(255),
    nsfw BOOLEAN,
    market_id VARCHAR(255),
    inverted BOOLEAN,
    username VARCHAR(255),
    profile_image VARCHAR(255),
    usd_market_cap FLOAT
);
```

``` sql
CREATE TABLE pump_fun_trade (
    id INT AUTO_INCREMENT PRIMARY KEY,
    signature VARCHAR(255) NOT NULL,
    mint VARCHAR(255) NOT NULL,
    sol_amount BIGINT NOT NULL,
    token_amount BIGINT NOT NULL,
    is_buy BOOLEAN NOT NULL,
    user VARCHAR(255) NOT NULL,
    timestamp BIGINT NOT NULL,
    tx_index INT NOT NULL,
    username VARCHAR(255),
    profile_image VARCHAR(255)
);
```

## 配置


```bash
# 配置 myenv 环境
python3 -m venv myenv
source myenv/bin/activate

# 安装依赖环境
pip3 install -r requirements.txt
```