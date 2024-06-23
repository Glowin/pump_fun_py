from db import MySQLDatabase
from rich.progress import Progress
from utils import Utils
import argparse
import multiprocessing

# Define a blacklist of mints
mint_blacklist = set([
    "FtQnb51TtSeNc2Tzn5yoG2LiDHodeu4imq2g9nvY6yL6",
])

# Argument parser to get proxy from command line
parser = argparse.ArgumentParser(description='Process proxy argument')
parser.add_argument('--proxy_list', default='None', help='proxy 的列表，用英文逗号区分, default is None')
parser.add_argument('--type', default='full', help='full: 全量更新, is_null: last_trade_timestamp is null, new: 最新交易的时间的coin列表有更新,需要更新 trade 记录; quick: 更新最新的数据，方便快速决策;')
args = parser.parse_args()

def update_mint_trade_info(m_list, proxy_info):
    with Progress() as progress:
        task = progress.add_task(f"[green]Processing mints... (PID: {multiprocessing.current_process().pid})", total=len(m_list))
        utils = Utils()
        _d_b = MySQLDatabase()
        _d_b.connect()
        for mint_info in m_list:
            mint, creator, symbol = mint_info['mint'], mint_info['creator'], mint_info['symbol']
            coin_data = utils.get_coin_data(mint, proxy_info)
            last_trade_timestamp = utils.get_trade_list(mint, creator, symbol, proxy=proxy_info)
            coin_data['last_trade_timestamp'] = last_trade_timestamp
            _d_b.update_mint(coin_data)
            if last_trade_timestamp:
                print(f"{symbol} | (PID: {multiprocessing.current_process().pid}) Successfully recorded trade data")
            else:
                print(f"{symbol} | (PID: {multiprocessing.current_process().pid}) Failed to record trade data for ")
            progress.advance(task)
        _d_b.disconnect()

if __name__ == '__main__':
    # Initialize the database connection
    db = MySQLDatabase()
    db.connect()

    if args.type == 'full':
        # Fetch the full mint list
        mint_list = db.get_full_mint_list()
    elif args.type == 'is_null':
        mint_list = db.get_is_null_mint_list()
    elif args.type == 'new':
        mint_list = db.get_new_mint_list(100)
    elif args.type == 'quick':
        quick_mint_list = db.get_quick_mint_list(50) # 最新更新 pump_fun_mint 中 last_trade_timestamp 的 mint
        top_in_5_min_mint_list = db.get_top_in_min_mint_list(5, 50) # 最近5分钟纯流入sol的前50名
        top_in_10_min_mint_list = db.get_top_in_min_mint_list(10, 50) # 最近10分钟纯流入sol的前50名
        # Combine the lists and remove duplicates based on the 'mint' key
        combined_mint_list = quick_mint_list + top_in_5_min_mint_list + top_in_10_min_mint_list
        unique_mint_list = {mint_info['mint']: mint_info for mint_info in combined_mint_list}.values()
        mint_list = list(unique_mint_list)
    
    # Disconnect from the database
    db.disconnect()

    # Filter out mints that are in the blacklist
    mint_list = [mint_info for mint_info in mint_list if mint_info['mint'] not in mint_blacklist]

    while True:
        procs = []
        p_list = args.proxy_list.split(',') if ',' in args.proxy_list else [args.proxy_list]
        p_count = len(p_list)

        for i in range(p_count):
            tmp_list = mint_list[i::p_count]
            tmp_proxy = p_list[i]
            procs.append(multiprocessing.Process(target=update_mint_trade_info, args=(tmp_list, tmp_proxy)))

        for proc in procs:
            proc.start()
        for proc in procs:
            proc.join()
