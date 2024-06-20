from db import MySQLDatabase
from rich.progress import Progress
from utils import get_trade_list, get_coin_data
import argparse

# Initialize the database connection
db = MySQLDatabase()
db.connect()

# Argument parser to get proxy from command line
parser = argparse.ArgumentParser(description='Process proxy argument')
parser.add_argument('--proxy', default='None', help='proxy for pump_fun api, default is None')
parser.add_argument('--type', default='full', help='full: 全量更新, is_null: last_trade_timestamp is null, new: 最新交易的时间的coin列表有更新，需要更新 trade 记录')
args = parser.parse_args()

while(1):
    if args.type == 'full':
        # Fetch the full mint list
        mint_list = db.get_full_mint_list()
    elif args.type == 'is_null':
        mint_list = db.get_is_null_mint_list()
    elif args.type == 'new':
        mint_list = db.get_new_mint_list()

    with Progress() as progress:
        task = progress.add_task("[green]Processing mints...", total=len(mint_list))
        
        for mint_info in mint_list:
            mint, creator, symbol = mint_info['mint'], mint_info['creator'], mint_info['symbol']
            coin_data = get_coin_data(mint, args.proxy)
            last_trade_timestamp = get_trade_list(mint, creator, symbol, proxy=args.proxy)
            coin_data['last_trade_timestamp'] = last_trade_timestamp
            db.update_mint(coin_data)
            if last_trade_timestamp:
                print(f"Successfully recorded trade data for symbol: {symbol}")
            else:
                print(f"Failed to record trade data for symbol: {symbol}")
            progress.advance(task)

# Disconnect from the database
db.disconnect()
