from flask import Blueprint

system_bp = Blueprint('system', __name__, 
                     template_folder='../templates')

from . import routes
