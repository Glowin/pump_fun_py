from db import MySQLDatabase
from utils import get_trade_list

# Establish a database connection
db = MySQLDatabase()
db.connect()

# Retrieve all mints that need to be checked for rugs
mints = db.get_rug_checklist()

# Record trade data for each mint in the database
for mint in mints:
    success = get_trade_list(mint)
    if success:
        print(f"Successfully recorded trade data for mint: {mint}")
    else:
        print(f"Failed to record trade data for mint: {mint}")

# Disconnect from the database
db.disconnect()

