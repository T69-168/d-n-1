import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'quan-ly-kho-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'kho.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOW_STOCK_THRESHOLD = 10
    JSON_AS_ASCII = False          # Fix tiếng Việt trong JSON
    JSONIFY_MIMETYPE = 'application/json; charset=utf-8'
