import json
import time
import requests
from config import RPC, PUB_KEY, client
from solana.transaction import Signature
from db import MySQLDatabase
import asyncio
from tg_bot import TelegramBot
from datetime import datetime, timedelta

# Initialize the database connection
db = MySQLDatabase()

URL_PREFIX = "https://frontend-api.pump.fun"

class Utils:
    def __init__(self):
        self.tg_bot = TelegramBot()
        self.smart_wallets = set()
        self.load_smart_wallets()

    def load_smart_wallets(self):
        db.connect()
        smart_wallets = db.get_smart_wallets()
        self.smart_wallets = set(wallet['address'] for wallet in smart_wallets)
        db.disconnect()

    async def send_telegram_message(self, message):
        await self.tg_bot.send_message(message)
    
    @staticmethod
    def find_data(data, field):
        if isinstance(data, dict):
            if field in data:
                return data[field]
            else:
                for value in data.values():
                    result = Utils.find_data(value, field)
                    if result is not None:
                        return result
        elif isinstance(data, list):
            for item in data:
                result = Utils.find_data(item, field)
                if result is not None:
                    return result
        return None

    @staticmethod
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
            ui_amount = Utils.find_data(response.json(), "uiAmount")
            return float(ui_amount)
        except Exception as e:
            return None

    @staticmethod
    def get_coin_data(mint_str, proxy):
        url = f"{URL_PREFIX}/coins/{mint_str}"
        headers = {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cache-control': 'no-cache',
            'origin': 'https://www.pump.fun',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': 'https://www.pump.fun/',
            'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        }
        if proxy and proxy != 'None':
            proxies = {
                'http': 'socks5h://' + proxy,
                'https': 'socks5h://' + proxy,
            }
        else:
            proxies = None

        retries = 0
        max_retries = 3
        response = None  # Ensure response is defined
        while retries < max_retries:
            try:
                response = requests.get(url, headers=headers, proxies=proxies, timeout=3)
                response.raise_for_status()  # Check for HTTP errors
                if response.status_code == 200:
                    break
            except (requests.exceptions.RequestException, requests.exceptions.ProxyError) as e:
                retries += 1
                print(f"get_coin_data Connection issue. Retrying {retries}/{max_retries}...")
                print(str(e))
                # Check for specific SOCKS5 proxy error
                if "Failed to establish a new connection: SOCKS5 proxy server sent invalid data" in str(e):
                    print("SOCKS5 proxy server sent invalid data. Aborting retries.")
                    return None
                time.sleep(1)
        else:
            print("Max retries exceeded. No successful connection.")
            return None

        try:
            if response.status_code == 200:
                coin_data = response.json()
                return coin_data
            else:
                return None
        except requests.exceptions.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return None

    @staticmethod
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
            'limit': '50',
            'sort': sort, # last_trade_timestamp, last_reply, reply_count, market_cap, created_timestamp
            'order': order,
            'includeNsfw': 'false',
        }
        if proxy and proxy != 'None':
            proxies = {
                'http': 'socks5h://' + proxy,
                'https': 'socks5h://' + proxy,
            }
        else:
            proxies = None

        retries = 0
        max_retries = 1
        response = None  # Ensure response is defined
        while retries < max_retries:
            try:
                response = requests.get(f'{URL_PREFIX}/coins', params=params, headers=headers, proxies=proxies)
                response.raise_for_status()  # Check for HTTP errors
                break
            except requests.exceptions.RequestException as e:
                retries += 1
                print(f"get_coin_list Connection issue. Retrying {retries}/{max_retries}...")
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
                        if db.check_mint_exists(coin['mint']) and sort == 'created_timestamp':
                            continue
                        elif db.check_mint_exists(coin['mint']) and sort == 'last_trade_timestamp':
                            db.update_mint(coin)
                        else:
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

    @staticmethod
    def escape_markdown(text):
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        return ''.join('\\' + char if char in special_chars else char for char in str(text))

    @staticmethod
    def format_timestamp(timestamp):
        utc_time = datetime.utcfromtimestamp(timestamp)
        utc_8_time = utc_time + timedelta(hours=8)
        return utc_8_time.strftime('%Y-%m-%d %H:%M:%S')

    def get_trade_list(self, mint, creator, symbol, proxy):
        if self.tg_bot is None:
            self.tg_bot = TelegramBot(proxy)
        max_retries = 1
        trade_page = 1
        offset = 0
        page_size = 100
        trade_list = []
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Origin': 'https://pump.fun',
            'Pragma': 'no-cache',
            'Referer': 'https://pump.fun/',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        }
        for _ in range(trade_page):
            url = f'{URL_PREFIX}/trades/{mint}?limit={page_size}&offset={offset}'
            if proxy and proxy != 'None':
                proxies = {
                    'http': 'socks5h://' + proxy,
                    'https': 'socks5h://' + proxy,
                }
            else:
                proxies = None

            retries = 0
            while retries < max_retries:
                try:
                    response = requests.get(url, headers=headers, proxies=proxies, timeout=3)
                    response.raise_for_status()  # Check for HTTP errors
                    break
                except requests.exceptions.RequestException as e:
                    retries += 1
                    print(f"Attempt {retries} failed: {proxy} {e}. Retrying...")
                    time.sleep(1 + retries*0.7)
            else:
                print("Max retries reached. Failed to fetch trade list.")
                return None
            
            if response.status_code == 200:
                try:
                    current_trade_list = response.json()
                    trade_list.extend(current_trade_list)
                    if len(current_trade_list) < page_size:
                        break
                    offset += page_size
                except ValueError as e:
                    print("Error parsing JSON response:", e)
                    return None
            else:
                return None
        
        db.connect()

        # 如果 creator rug 了，则记录到数据库中
        creator_buy_token = sum(trade['token_amount'] for trade in trade_list if trade['user'] == creator and trade['is_buy'] == 1)
        creator_sell_token = sum(trade['token_amount'] for trade in trade_list if trade['user'] == creator and trade['is_buy'] == 0)
        # Generate a list of users who have made buy trades (is_buy = 1)
        buy_users = set(trade['user'] for trade in trade_list if trade['is_buy'] == 1)
        # Calculate the sum of token_amount for sell trades (is_buy = 0) where the user is not in the buy_user list
        rat_sell_token = sum(trade['token_amount'] for trade in trade_list if trade['is_buy'] == 0 and trade['user'] not in buy_users)
        if rat_sell_token > 0:            
            # Print the result for verification
            print(f"Total rat sell token amount: {rat_sell_token}")
        if (creator_sell_token + rat_sell_token) > creator_buy_token * 0.5:
            if rat_sell_token > creator_buy_token * 0.3:
                db.update_rug_status(mint, 2)
                print(f"{symbol} rug!!! RAT!!!")
            else:
                db.update_rug_status(mint, 1)
                print(f"{symbol} rug!!!")
        else:
            db.update_rug_status(mint, 0)

        # Check for smart wallet trades
        messages = []
        for trade in trade_list:
            if trade['user'] in self.smart_wallets:
                # Insert the smart trade into the database
                smart_trade_data = {
                    'signature': trade['signature'],
                    'mint': trade['mint'],
                    'user': trade['user'],
                    'is_buy': trade['is_buy'],
                    'sol_amount': trade['sol_amount'] / 1e9,
                    'timestamp': trade['timestamp']
                }
                db.insert_smart_trade(smart_trade_data)

                # Check if message has been sent before
                if db.check_and_mark_message_sent(trade['signature']):
                    formatted_time = self.format_timestamp(trade['timestamp'])
                    message = f'''🚨 Smart Wallet Alert 🚨
Symbol: {self.escape_markdown(symbol)}
Mint: `{self.escape_markdown(trade['mint'])}`
User: {self.escape_markdown('...' + trade['user'][-6:])}
Action: {self.escape_markdown('Buy' if trade['is_buy'] else 'Sell')}
Amount: {self.escape_markdown(f"{trade['sol_amount'] / 1e9:.4f}")} SOL
Time \(UTC\+8\): {self.escape_markdown(formatted_time)}'''
                    messages.append(message)

        # Send all messages at once
        if messages:
            asyncio.run(self.send_all_messages(messages))

        # 批量记录交易到数据库中
        try:
            success = db.insert_trades_bulk(trade_list)
        except Exception as e:
            print(f"Error while inserting trade data: {e}")
            return False
        db.disconnect()
        if trade_list:
            return max(trade['timestamp'] for trade in trade_list) * 1000
        else:
            return None

    async def send_all_messages(self, messages):
        tasks = [self.send_telegram_message(message) for message in messages]
        await asyncio.gather(*tasks)

    @staticmethod
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
