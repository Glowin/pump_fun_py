from db import MySQLDatabase
from utils import Utils
import argparse

# Establish a database connection
db = MySQLDatabase()
db.connect()

# Argument parser
parser = argparse.ArgumentParser(description='Process arguments')
parser.add_argument('--proxy', default='None', help='proxy for pump_fun api, default is None')
parser.add_argument('--sort', default='DESC', help='sort')
parser.add_argument('--type', default='new', help='type, new 是最新的mint，check 是 rug is null 和 rug = 0')
args = parser.parse_args()

utils = Utils()

while(1):
    # Retrieve all mints that need to be checked for rugs
    mint_list = db.get_rug_checklist(args.sort, args.type)

    # Record trade data for each mint in the database
    for mint_info in mint_list:
        success = utils.get_trade_list(mint_info[0], mint_info[1], mint_info[2], proxy=args.proxy)
        if success:
            print(f"Successfully recorded trade data for symbol: {mint_info[2]}")
        else:
            print(f"Failed to record trade data for symbol: {mint_info[2]}")

# Disconnect from the database
db.disconnect()

