"""Flask app configuration."""
from os import environ, path
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))


class Config:
    """Set Flask configuration from environment variables."""
    FLASK_APP = 'worksreg.py'
    FLASK_ENV = environ.get('FLASK_ENV')
    SECRET_KEY = environ.get('SECRET_KEY')
    MAX_CONTENT_LENGTH = 1024 * 1024
    UPLOAD_EXTENSIONS = ['.csv']

    # Static Assets
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'

    # HDB
    HDB_URI=environ.get('HDB_URI')
    HDB_PWD=environ.get('HDB_PWD')
    HDB_USER=environ.get('HDB_USER')
    HDB_PORT=environ.get('HDB_PORT')
