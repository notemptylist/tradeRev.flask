import os
from flask import Blueprint, current_app as app, send_from_directory

static_folder = os.path.join('frontend', 'build')
bp = Blueprint('frontend', __name__, static_folder=static_folder)

@bp.route('/static/<path:path>')
def serve_static(path):
    print(f"Serving static path: '{path}'")
    actual_static_dir = os.path.join(bp.static_folder, 'static')
    target = os.path.join(bp.static_folder, 'static', path)
    if os.path.exists(target):
        return send_from_directory(actual_static_dir, path)

@bp.route('/', defaults={'path':''})
def serve(path):
    print(f"Serving / path: '{path}'")
    return send_from_directory(bp.static_folder, 'index.html')
