import math
import time
from db import MySQLDatabase
from datetime import datetime, timedelta
import multiprocessing
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WalletScorer:
    def __init__(self):
        self.lambda_param = 0.3  # 控制衰减速度
        self.plateau_days = 7  # 最近7天保持高权重
        self.high_frequency_threshold = 10  # 高频交易阈值，例如1分钟内超过10笔交易
        self.high_frequency_time_threshold = 60  # 高频交易时间阈值，单位为秒
        self.small_trade_threshold = 0.1  # 小额交易阈值，例如小于 0.1 SOL

    def calculate_time_weight(self, trade_timestamp, current_timestamp):
        days_passed = (current_timestamp - trade_timestamp) / 86400  # 转换为天数
        
        if days_passed <= self.plateau_days:
            # 最近7天内的交易保持最高权重
            return 1.0
        else:
            # 7天后开始指数衰减
            return math.exp(-self.lambda_param * (days_passed - self.plateau_days))

    def is_high_frequency_trading(self, trades):
        if len(trades) < self.high_frequency_threshold:
            return False
        trades.sort(key=lambda x: x['timestamp'])
        for i in range(len(trades) - self.high_frequency_threshold + 1):
            if trades[i + self.high_frequency_threshold - 1]['timestamp'] - trades[i]['timestamp'] < self.high_frequency_time_threshold:
                # 检查是否为小额交易
                if all(trade['sol_amount'] / 1e9 < self.small_trade_threshold for trade in trades[i:i + self.high_frequency_threshold]):
                    return True
        return False

    def calculate_score_and_pnl(self, wallet_address, db):
        current_timestamp = int(time.time())
        trades = db.get_wallet_trades(wallet_address)
        if not trades:
            return None

        score = 0
        pnl_1d = 0
        pnl_7d = 0
        pnl_30d = 0
        token_balances = {}
        rat_trade_count = 0  # 记录老鼠仓行为次数

        one_day_ago = current_timestamp - 86400
        seven_days_ago = current_timestamp - 604800
        thirty_days_ago = current_timestamp - 2592000

        trades_by_mint = {}
        for trade in trades:
            mint = trade['mint']
            if mint not in trades_by_mint:
                trades_by_mint[mint] = []
            trades_by_mint[mint].append(trade)

        for mint, mint_trades in trades_by_mint.items():
            if self.is_high_frequency_trading(mint_trades):
                continue

            mint_score = 0
            mint_balance = 0
            for trade in mint_trades:
                sol_amount = trade['sol_amount'] / 1e9  # Convert lamports to SOL
                token_amount = trade['token_amount'] / 1e6  # Correct the token amount
                is_buy = trade['is_buy']
                timestamp = trade['timestamp']
                creator = trade['creator']

                time_weight = self.calculate_time_weight(timestamp, current_timestamp)

                if is_buy:
                    trade_pnl = -sol_amount * 1.01  # 买入时，实际花费的 SOL 增加 1%
                else:
                    trade_pnl = sol_amount * 0.99  # 卖出时，实际获得的 SOL 减少 1%

                mint_balance += token_amount if is_buy else -token_amount

                if creator == wallet_address:
                    time_weight *= 1e-6  # 将创建者的惩罚权重设为 1e-6

                mint_score += trade_pnl * time_weight

                if timestamp >= one_day_ago:
                    pnl_1d += trade_pnl
                if timestamp >= seven_days_ago:
                    pnl_7d += trade_pnl
                if timestamp >= thirty_days_ago:
                    pnl_30d += trade_pnl

            if mint_balance < -100:  # 检测到老鼠仓行为
                rat_trade_count += 1
                db.insert_mint_to_trade_fix(mint)
                mint_score *= 0.1  # 对该代币的得分进行惩罚，而不是直接清零
            
            score += mint_score
            token_balances[mint] = mint_balance

        # 计算未实现的收益
        for mint, balance in token_balances.items():
            if balance > 0:
                last_trade = db.get_last_trade_for_mint(mint)
                if last_trade:
                    last_trade_token_amount = last_trade['token_amount'] / 1e6
                    last_trade_sol_amount = last_trade['sol_amount'] / 1e9
                    token_value = (balance / last_trade_token_amount) * last_trade_sol_amount
                    score += token_value

        # 根据老鼠仓行为次数进行整体惩罚
        rat_trade_penalty = min(1, rat_trade_count * 0.1)  # 每次老鼠仓行为增加10%的惩罚
        score -= abs(score) * rat_trade_penalty

        return {
            'address': wallet_address,
            'score': score,
            '1d_pnl': pnl_1d,
            '7d_pnl': pnl_7d,
            '30d_pnl': pnl_30d,
            'updatedAt': current_timestamp,
            'rat_trade_count': rat_trade_count
        }

    def process_wallets(self, start_offset, end_offset):
        db = MySQLDatabase()
        db.connect()
        
        offset = start_offset
        batch_size = 50000
        
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

def run_scoring_cycle():
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

def main():
    while True:
        start_time = time.time()
        logging.info("Starting a new scoring cycle")
        
        run_scoring_cycle()
        
        end_time = time.time()
        duration = end_time - start_time
        logging.info(f"Scoring cycle completed in {duration:.2f} seconds")
        
        wait_time = max(3600 - duration, 0)
        logging.info(f"Waiting for {wait_time:.2f} seconds before starting next cycle")
        time.sleep(wait_time)

if __name__ == "__main__":
    main()