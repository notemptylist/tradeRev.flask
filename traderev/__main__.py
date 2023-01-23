import os
import sys
import configparser

__package__ = 'traderev'
from traderev import create_app
mongo_config_fmt = """[default]
mongo_uri=<url>
db_name=traderev
transactions_col=transactions
"""

config_file = os.environ.get('MONGO_INI', None)
if not config_file:
    print("MONGO_INI environment variable needs to be set to a mongo config file.")
    print("Using the following format:")
    print(mongo_config_fmt)
    sys.exit(1)

config = configparser.ConfigParser()
config.read(config_file)
if __name__ == "__main__":
    app = create_app()
    # app.config['DEBUG'] = True
    app.config['MONGO_URI'] = config['default']['mongo_uri']

    app.run()