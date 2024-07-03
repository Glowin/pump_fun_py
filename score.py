from datetime import datetime, timedelta
import numpy as np
from db import MySQLDatabase

def calculate_wallet_pnl_and_score(wallet_address, db):
    wallet_trades = db.get_wallet_trades(wallet_address)
    if not wallet_trades:
        return {'address': wallet_address, 'score': 0, '1d_pnl': 0, '7d_pnl': 0, '30d_pnl': 0}

    total_score = 0
    total_pnl = { '1d': 0, '7d': 0, '30d': 0 }
    sol_balance = { '1d': 0, '7d': 0, '30d': 0, 'all': 0 }
    current_time = datetime.now().timestamp()

    # 时间范围
    time_ranges = {
        '1d': current_time - timedelta(days=1).total_seconds(),
        '7d': current_time - timedelta(days=7).total_seconds(),
        '30d': current_time - timedelta(days=30).total_seconds(),
    }

    for trade in wallet_trades:
        mint_info = db.get_mint_info(trade['mint'])
        if not mint_info:
            continue
        mint_info = mint_info[0]
        is_creator = (mint_info['creator'] == wallet_address)

        # 盈利计算
        trade_value = trade['sol_amount'] / 1e9  # Assuming sol_amount is in lamports
        if trade['is_buy']:
            sol_balance['all'] -= trade_value
        else:
            sol_balance['all'] += trade_value

        # 时间权重计算
        time_diff = current_time - trade['timestamp']
        time_weight = np.exp(-time_diff / (365 * 24 * 60 * 60))  # 按年衰减

        # Creator 影响计算
        if is_creator:
            trade_value *= 0.5  # 假设 creator 影响为50%

        # 累加到总得分
        total_score += trade_value * time_weight

        # 分别计算1d, 7d, 30d的PNL
        for period, start_time in time_ranges.items():
            if trade['timestamp'] >= start_time:
                if trade['is_buy']:
                    sol_balance[period] -= trade_value
                else:
                    sol_balance[period] += trade_value
                total_pnl[period] += trade_value

    # 考虑未卖出的代币余额
    total_score += sol_balance['all']
    pnl_1d = total_pnl['1d'] + sol_balance['1d']
    pnl_7d = total_pnl['7d'] + sol_balance['7d']
    pnl_30d = total_pnl['30d'] + sol_balance['30d']

    return {'address': wallet_address, 'score': total_score, '1d_pnl': pnl_1d, '7d_pnl': pnl_7d, '30d_pnl': pnl_30d, 'updatedAt': int(current_time)}

if __name__ == '__main__':
    db = MySQLDatabase()
    db.connect()
    
    offset = 0
    batch_size = 100
    
    while True:
        wallet_addresses = db.get_unique_wallet_addresses_batch(offset, batch_size)
        if not wallet_addresses:
            break
        
        for wallet in wallet_addresses:
            wallet_address = wallet['user']
            result = calculate_wallet_pnl_and_score(wallet_address, db)
            db.upsert_wallet_score(result)  # 计算后立即保存到数据库

        offset += batch_size

    db.disconnect()