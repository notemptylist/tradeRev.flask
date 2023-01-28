import os
import sys
import configparser
from flask import Flask, redirect
from werkzeug.middleware.profiler import ProfilerMiddleware
from .utils import CustomJSONEncoder

mongo_config_fmt = """[default]
mongo_uri=<url>
db_name=traderev
transactions_col=transactions
"""

def create_app(test_config=None):
    """Flask app factory"""
    app = Flask(__name__,
                instance_relative_config=True,
                static_url_path='')
    app.config.from_mapping(SECRET_KEY='dev',
    )
    if test_config:
        app.config.from_mapping(test_config)
    else:
        app.config.from_pyfile('config.py', silent=True)

    profiles_path = os.path.join(app.instance_path, 'profiles')
    try:
        os.makedirs(app.instance_path)
    except OSError as e:
        pass

    try:
        os.makedirs(profiles_path)
    except OSError as e:
        pass

    from . import api
    from . import frontend
    app.register_blueprint(api.bp)
    app.register_blueprint(frontend.bp)
    # @app.errorhandler(404)
    # def not_found_redirect(e):
    #     return redirect('/', 302)
    # app.wsgi_app = ProfilerMiddleware(app.wsgi_app, profile_dir=profiles_path)

    config_file = os.environ.get('MONGO_INI', None)
    if not config_file:
        print("MONGO_INI environment variable needs to be set to a mongo config file.")
        print("Using the following format:")
        print(mongo_config_fmt)
        sys.exit(1)

    app.json_encoder = CustomJSONEncoder
    config = configparser.ConfigParser()
    config.read(config_file)
    app.config['MONGO_URI'] = config['default']['mongo_uri']
    return app