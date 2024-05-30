import json
import time
import base58
import requests
from config import RPC, PUB_KEY, client
from solana.transaction import Signature
from db import MySQLDatabase

# Initialize the database connection
db = MySQLDatabase()

def find_data(data, field):
    if isinstance(data, dict):
        if field in data:
            return data[field]
        else:
            for value in data.values():
                result = find_data(value, field)
                if result is not None:
                    return result
    elif isinstance(data, list):
        for item in data:
            result = find_data(item, field)
            if result is not None:
                return result
    return None

def get_token_balance(base_mint: str):
    try:

        headers = {"accept": "application/json", "content-type": "application/json"}

        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "getTokenAccountsByOwner",
            "params": [
                PUB_KEY,
                {"mint": base_mint},
                {"encoding": "jsonParsed"},
            ],
        }
        
        response = requests.post(RPC, json=payload, headers=headers)
        ui_amount = find_data(response.json(), "uiAmount")
        return float(ui_amount)
    except Exception as e:
        return None

def get_coin_data(mint_str, proxy):
    url = f"https://client-api-2-74b1891ee9f9.herokuapp.com/coins/{mint_str}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.pump.fun/",
        "Origin": "https://www.pump.fun",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "If-None-Match": 'W/"43a-tWaCcS4XujSi30IFlxDCJYxkMKg"'
    }
    if proxy:
        proxies = {
            'http': 'socks5h://' + proxy,
            'https': 'socks5h://' + proxy,
        }
    else:
        proxies = None

    response = requests.get(url, headers=headers, proxies=proxies)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_coin_list(sort='created_timestamp', order='DESC', proxy=None):
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Origin': 'https://pump.fun',
        'Pragma': 'no-cache',
        'Referer': 'https://pump.fun/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
    }
    params = {
        'offset': '0',
        'limit': '10',
        'sort': sort, # last_trade_timestamp, last_reply, reply_count, market_cap, created_timestamp
        'order': order,
        'includeNsfw': 'false',
    }
    if proxy:
        proxies = {
            'http': 'socks5h://' + proxy,
            'https': 'socks5h://' + proxy,
        }
    else:
        proxies = None

    retries = 0
    max_retries = 30
    response = None  # Ensure response is defined
    while retries < max_retries:
        try:
            response = requests.get('https://client-api-2-74b1891ee9f9.herokuapp.com/coins', params=params, headers=headers, proxies=proxies)
            response.raise_for_status()  # Check for HTTP errors
            break
        except requests.exceptions.RequestException as e:
            retries += 1
            print(f"Connection issue. Retrying {retries}/{max_retries}...")
            print(str(e))
            time.sleep(1)
    else:
        return None

    if response.status_code == 200:
        try:
            coin_list = response.json()
            
            db.connect()
            for coin in coin_list:
                try:
                    if db.check_mint_exists(coin['mint']):
                        continue
                    success = db.pump_fun_mint_insert(coin)
                except Exception as e:
                    print(f"Error while inserting token data: {e}")
                    return False
            db.disconnect()
        except ValueError as e:
            print("Error parsing JSON response:", e)
            return None
    else:
        return None

def get_trade_list(mint, creator, symbol, proxy):
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Origin': 'https://pump.fun',
        'Pragma': 'no-cache',
        'Referer': 'https://pump.fun/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
    }
    url = f'https://client-api-2-74b1891ee9f9.herokuapp.com/trades/{mint}?limit=200&offset=0'
    if proxy and proxy != 'None':
        proxies = {
            'http': 'socks5h://' + proxy,
            'https': 'socks5h://' + proxy,
        }
    else:
        proxies = None

    retries = 0
    max_retries = 10
    while retries < max_retries:
        try:
            response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
            response.raise_for_status()  # Check for HTTP errors
            break
        except requests.exceptions.RequestException as e:
            retries += 1
            print(f"Attempt {retries} failed: {e}. Retrying...")
            time.sleep(1)
    else:
        print("Max retries reached. Failed to fetch trade list.")
        return None
    
    if response.status_code == 200:
        try:
            trade_list = response.json()
            
            db.connect()

            # 如果 creator rug 了，则记录到数据库中
            creator_buy_sol = sum(trade['sol_amount'] for trade in trade_list if trade['user'] == creator and trade['is_buy'] == 1)
            creator_sell_sol = sum(trade['sol_amount'] for trade in trade_list if trade['user'] == creator and trade['is_buy'] == 0)
            # Generate a list of users who have made buy trades (is_buy = 1)
            buy_users = set(trade['user'] for trade in trade_list if trade['is_buy'] == 1)
            # Calculate the sum of sol_amount for sell trades (is_buy = 0) where the user is not in the buy_user list
            rat_sell_sol = sum(trade['sol_amount'] for trade in trade_list if trade['is_buy'] == 0 and trade['user'] not in buy_users)
            if rat_sell_sol > 0:            
                # Print the result for verification
                print(f"Total rat sell sol amount: {rat_sell_sol}")
            if (creator_sell_sol + rat_sell_sol) > creator_buy_sol * 0.5:
                db.update_rug_status(mint, 1)
                print(f"{symbol} rug!!!")
            else:
                db.update_rug_status(mint, 0)

            # 记录每条交易到数据库中
            for trade in trade_list:
                try:
                    if db.check_trade_exists(trade['signature']):
                        continue
                    success = db.insert_trade(trade)
                except Exception as e:
                    print(f"Error while inserting trade data: {e}")
                    return False
            return True
            db.disconnect()
        except ValueError as e:
            print("Error parsing JSON response:", e)
            return None
    else:
        return None

def confirm_txn(txn_sig, max_retries=20, retry_interval=3):
    retries = 0
    if isinstance(txn_sig, str):
        txn_sig = Signature.from_string(txn_sig)
    while retries < max_retries:
        try:
            txn_res = client.get_transaction(txn_sig, encoding="json", commitment="confirmed", max_supported_transaction_version=0)
            txn_json = json.loads(txn_res.value.transaction.meta.to_json())
            if txn_json['err'] is None:
                print("Transaction confirmed... try count:", retries+1)
                return True
            print("Error: Transaction not confirmed. Retrying...")
            if txn_json['err']:
                print("Transaction failed.")
                return False
        except Exception as e:
            print("Awaiting confirmation... try count:", retries+1)
            retries += 1
            time.sleep(retry_interval)
    print("Max retries reached. Transaction confirmation failed.")
    return None
