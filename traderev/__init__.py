import os
from flask import Flask, Blueprint
from werkzeug.middleware.profiler import ProfilerMiddleware


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
    # app.wsgi_app = ProfilerMiddleware(app.wsgi_app, profile_dir=profiles_path)
    return app