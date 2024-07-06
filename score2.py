import time
from db import MySQLDatabase
from datetime import datetime, timedelta
import multiprocessing
import os

class WalletScorer:
    def __init__(self):
        self.current_timestamp = int(time.time())

    def calculate_score_and_pnl(self, wallet_address, db):
        trades = db.get_wallet_trades(wallet_address)
        if not trades:
            return None

        score = 0
        pnl_1d = 0
        pnl_7d = 0
        pnl_30d = 0
        token_balances = {}

        one_day_ago = self.current_timestamp - 86400
        seven_days_ago = self.current_timestamp - 604800
        thirty_days_ago = self.current_timestamp - 2592000

        for trade in trades:
            mint = trade['mint']
            sol_amount = trade['sol_amount'] / 1e9  # Convert lamports to SOL
            is_buy = trade['is_buy']
            timestamp = trade['timestamp']
            creator = trade['creator']

            time_weight = 1 / (1 + (self.current_timestamp - timestamp) / (86400*7))

            if creator == wallet_address:
                time_weight *= 0.001

            trade_pnl = -sol_amount * 1.01 if is_buy else sol_amount * 0.99

            if mint not in token_balances:
                token_balances[mint] = 0
            token_balances[mint] += trade['token_amount'] if is_buy else -trade['token_amount']

            score += trade_pnl * time_weight

            if timestamp >= one_day_ago:
                pnl_1d += trade_pnl
            if timestamp >= seven_days_ago:
                pnl_7d += trade_pnl
            if timestamp >= thirty_days_ago:
                pnl_30d += trade_pnl

        for mint, balance in token_balances.items():
            if balance > 0:
                last_trade = db.get_last_trade_for_mint(mint)
                if last_trade:
                    token_value = (balance / last_trade['token_amount']) * (last_trade['sol_amount'] / 1e9)
                    score += token_value

        return {
            'address': wallet_address,
            'score': score,
            '1d_pnl': pnl_1d,
            '7d_pnl': pnl_7d,
            '30d_pnl': pnl_30d,
            'updatedAt': self.current_timestamp
        }

    def process_wallets(self, start_offset, end_offset):
        db = MySQLDatabase()
        db.connect()
        
        offset = start_offset
        batch_size = 100
        
        while offset < end_offset:
            wallets = db.get_unique_wallet_addresses_batch(offset, batch_size)
            if not wallets:
                break

            for wallet in wallets:
                result = self.calculate_score_and_pnl(wallet['user'], db)
                if result:
                    print(str(result))
                    db.upsert_wallet_score(result)

            offset += batch_size

        db.disconnect()

def run_process(start_offset, end_offset):
    scorer = WalletScorer()
    scorer.process_wallets(start_offset, end_offset)

def main():
    db = MySQLDatabase()
    db.connect()
    total_wallets = db.get_total_unique_wallets()
    db.disconnect()

    num_processes = os.cpu_count()  # 获取CPU核心数
    chunk_size = total_wallets // num_processes
    
    processes = []
    for i in range(num_processes):
        start_offset = i * chunk_size
        end_offset = start_offset + chunk_size if i < num_processes - 1 else total_wallets
        p = multiprocessing.Process(target=run_process, args=(start_offset, end_offset))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

if __name__ == "__main__":
    main()