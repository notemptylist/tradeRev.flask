import os
from flask import Flask

def create_app(test_config=None):
    """Flask app factory"""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY="dev",
    )
    if test_config: 
        app.config.from_mapping(test_config)
    else:
        app.config.from_pyfile('config.py', silent=True)
    
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import api
    app.register_blueprint(api.bp)
    return app