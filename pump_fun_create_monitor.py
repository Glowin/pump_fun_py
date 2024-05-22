from utils import get_coin_list
import argparse
import time

# Argument parser
parser = argparse.ArgumentParser(description='Process sort and order arguments')
parser.add_argument('--sort', default='created_timestamp', help='the field to sort by, default is created_timestamp')
parser.add_argument('--order', default='DESC', help='the sort order, default is DESC')
args = parser.parse_args()

while(1):
    get_coin_list(sort=args.sort, order=args.order)
    time.sleep(1)
