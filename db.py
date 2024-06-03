import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
MYSQL_PORT = os.getenv("MYSQL_PORT")

class MySQLDatabase:
    def __init__(self, host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DATABASE, port=MYSQL_PORT):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
    
    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
        except mysql.connector.Error as err:
            print(f"Error: '{err}'")
            self.connection = None
    
    def disconnect(self):
        if self.connection:
            self.connection.close()
        else:
            print("Connection is already closed or not established")
    
    def execute_query(self, query):
        if not self.connection:
            print("Not connected to any database.")
            return None
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            self.connection.commit()
            print("Query executed successfully")
            return cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Error: '{err}'")
            return None
        finally:
            cursor.close()

    def execute_update(self, query):
        if not self.connection:
            print("Not connected to any database.")
            return False
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            self.connection.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Error: '{err}'")
            return False
        finally:
            cursor.close()

    def pump_fun_mint_insert(self, data):
        if not self.connection:
            print("Not connected to any database.")
            return False
        
        cursor = self.connection.cursor()
        
        query = """
        INSERT INTO pump_fun_mint (
            mint, name, symbol, description, image_uri, metadata_uri, twitter,
            telegram, bonding_curve, associated_bonding_curve, creator,
            created_timestamp, raydium_pool, complete, virtual_sol_reserves,
            virtual_token_reserves, hidden, total_supply, website, show_name,
            last_trade_timestamp, king_of_the_hill_timestamp, market_cap,
            reply_count, last_reply, nsfw, market_id, inverted, username,
            profile_image, usd_market_cap
        ) VALUES (
            %(mint)s, %(name)s, %(symbol)s, %(description)s, %(image_uri)s, %(metadata_uri)s,
            %(twitter)s, %(telegram)s, %(bonding_curve)s, %(associated_bonding_curve)s, %(creator)s,
            %(created_timestamp)s, %(raydium_pool)s, %(complete)s, %(virtual_sol_reserves)s,
            %(virtual_token_reserves)s, %(hidden)s, %(total_supply)s, %(website)s, %(show_name)s,
            %(last_trade_timestamp)s, %(king_of_the_hill_timestamp)s, %(market_cap)s,
            %(reply_count)s, %(last_reply)s, %(nsfw)s, %(market_id)s, %(inverted)s, %(username)s,
            %(profile_image)s, %(usd_market_cap)s
        )
        """

        for key in ['hidden', 'last_trade_timestamp', 'username', 'profile_image']:
            if key not in data:
                data[key] = None
        
        try:
            cursor.execute(query, data)
            self.connection.commit()
            print(f"{data['symbol']} inserted successfully into pump_fun_mint table")
            return True
        except mysql.connector.Error as err:
            print(f"Error: '{err}'")
            return False
        finally:
            cursor.close()

    def check_mint_exists(self, mint):
        """
        Check if a mint exists in the pump_fun_mint table.
        
        Args:
            mint (str): The mint value to check in the table.

        Returns:
            bool: True if mint exists, False otherwise.
        """
        if not self.connection:
            print("Not connected to any database.")
            return False

        cursor = self.connection.cursor()
        query = "SELECT COUNT(*) FROM pump_fun_mint WHERE mint = %s"
        
        try:
            cursor.execute(query, (mint,))
            result = cursor.fetchone()
            exists = result[0] > 0
            return exists
        except mysql.connector.Error as err:
            print(f"Error: '{err}'")
            return False
        finally:
            cursor.close()

    def check_trade_exists(self, signature):
        """
        Check if a trade exists in the pump_fun_trade table.
        
        Args:
            signature (str): The trade signature to check in the table.

        Returns:
            bool: True if trade exists, False otherwise.
        """
        if not self.connection:
            print("Not connected to any database.")
            return False

        cursor = self.connection.cursor()
        query = "SELECT COUNT(*) FROM pump_fun_trade WHERE signature = %s"
        
        try:
            cursor.execute(query, (signature,))
            result = cursor.fetchone()
            exists = result[0] > 0
            return exists
        except mysql.connector.Error as err:
            print(f"Error: '{err}'")
            return False
        finally:
            cursor.close()

    def insert_trade(self, data):
        """
        Insert a trade record into the pump_fun_trade table.

        Args:
            data (dict): The trade data to insert into the table.

        Returns:
            bool: True if the insertion was successful, False otherwise.
        """
        if not self.connection:
            print("Not connected to any database.")
            return False

        cursor = self.connection.cursor()
        query = """
            INSERT INTO pump_fun_trade (
                signature, mint, sol_amount, token_amount, is_buy, user, 
                timestamp, tx_index, username, profile_image
            )
            VALUES (%(signature)s, %(mint)s, %(sol_amount)s, %(token_amount)s, %(is_buy)s, %(user)s, %(timestamp)s, %(tx_index)s, %(username)s, %(profile_image)s)
        """
        
        try:
            cursor.execute(query, data)
            self.connection.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Error: '{err}'")
            return False
        finally:
            cursor.close()

    def get_rug_checklist(self):
        """
        Get a list of mints from the pump_fun_mint table where the rug field is NULL.
        
        Returns:
            list: A list of mints where the rug field is NULL.
        """
        if not self.connection:
            print("Not connected to any database.")
            return []

        cursor = self.connection.cursor()
        query = "SELECT mint, creator, symbol FROM pump_fun_mint WHERE rug IS NULL OR rug = 0 ORDER BY created_timestamp DESC limit 100"

        try:
            cursor.execute(query)
            result = cursor.fetchall()
            return [(row[0], row[1], row[2]) for row in result]
        except mysql.connector.Error as err:
            print(f"Error: '{err}'")
            return []
        finally:
            cursor.close()

    def get_mints_with_null_or_zero_rug(self):
        """
        Get a list of tuples containing the symbol and creator from the pump_fun_mint table 
        where the rug field is NULL or 0.

        Returns:
            list: A list of tuples (symbol, creator) where the rug field is NULL or 0.
        """
        if not self.connection:
            print("Not connected to any database.")
            return []

        cursor = self.connection.cursor()
        query = "SELECT symbol, creator FROM pump_fun_mint WHERE rug IS NULL OR rug = 0"

        try:
            cursor.execute(query)
            result = cursor.fetchall()
            return [(row[0], row[1]) for row in result]
        except mysql.connector.Error as err:
            print(f"Error: '{err}'")
            return []
        finally:
            cursor.close()

    def get_trade_by_mint_and_creator(self, mint, creator):
        """
        Get a list of tuples containing the sol_amount and is_buy from the pump_fun_trade table 
        where the mint is equal to the provided mint and the user is equal to the provided creator.

        Args:
            mint (str): The mint to search for.
            creator (str): The creator(user) to search for.

        Returns:
            list: A list of tuples (sol_amount, is_buy) where the mint and user match the arguments.
        """
        if not self.connection:
            print("Not connected to any database.")
            return []

        cursor = self.connection.cursor()
        query = """
            SELECT sol_amount, is_buy 
            FROM pump_fun_trade 
            WHERE mint = %s AND user = %s
        """

        try:
            cursor.execute(query, (mint, creator))
            result = cursor.fetchall()
            return [(row[0], row[1]) for row in result]
        except mysql.connector.Error as err:
            print(f"Error: '{err}'")
            return []
        finally:
            cursor.close()

    def update_rug_status(self, mint, rug_status):
        """
        Updates the rug status in the pump_fun_mint table for a given mint.

        Args:
            mint (str): The mint to update.
            rug_status (bool): The new rug status to set.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        if not self.connection:
            print("Not connected to any database.")
            return False

        cursor = self.connection.cursor()
        query = """
            UPDATE pump_fun_mint
            SET rug = %s
            WHERE mint = %s
        """
        try:
            cursor.execute(query, (rug_status, mint))
            self.connection.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Error: '{err}'")
            self.connection.rollback()
            return False
        finally:
            cursor.close()



    def __del__(self):
        self.disconnect()

# Example usage:
# db = MySQLDatabase(host="localhost", user="root", password="password", database="test_db")
# db.connect()
# db.execute_query("SELECT * FROM users")
# db.disconnect()
