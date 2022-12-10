import configparser

from traderev import create_app

config = configparser.ConfigParser()
config.read('.ini')
if __name__ == "__main__":
    app = create_app()
    app.config['DEBUG'] = True
    app.config['MONGO_URI'] = config['default']['mongo_uri']

    app.run()