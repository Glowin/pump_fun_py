from utils import Utils
import argparse
import time

# Argument parser
parser = argparse.ArgumentParser(description='Process sort and order arguments')
parser.add_argument('--sort', default='created_timestamp', help='created_timestamp: 按照发布时间, last_trade_timestamp: 按照最新交易的时间')
parser.add_argument('--order', default='DESC', help='the sort order, default is DESC')
parser.add_argument('--proxy', default='None', help='proxy for pump_fun api, default is None')
args = parser.parse_args()

utils = Utils()

while(1):
    utils.get_coin_list(sort=args.sort, order=args.order, proxy=args.proxy)
