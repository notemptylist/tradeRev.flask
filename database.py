from pymongo import MongoClient

import configparser

config = configparser.ConfigParser()
config.read('mongo.ini')
mongo_uri = config['default']['mongo_uri']
db_name = config['default']['db_name']
transactions_col = config['default']['transactions_col']

client = MongoClient(mongo_uri)
db = client.get_database(db_name)
trans_col = db[transactions_col]