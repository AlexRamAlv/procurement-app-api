import os
import configparser

config = configparser.ConfigParser()
basedir = os.path.abspath(os.path.dirname(__file__))
config_dir = os.path.join(basedir, "config.ini")
config.read(config_dir)


class AppSettings:
    # Env variables
    # -- Secret Key
    SECRET_KEY = config.get("secret", "SECRET_KEY") or "hard to guess string"
    # -- Database
    DATABASE_URI = config.get("db", "DATABASE_URI")

    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    ALGORITHM = "HS256"


class MailConfig:
    # -- Mail config
    MAIL_SERVER = config.get("email", "MAIL_SERVER")
    MAIL_PORT = config.getint("email", "MAIL_PORT")
    MAIL_SSL_TLS = config.getboolean("email", "MAIL_SSL_TLS")
    MAIL_STARTTLS = config.getboolean("email", "MAIL_STARTTLS")
    USE_CREDENTIALS = config.getboolean("email", "USE_CREDENTIALS")
    VALIDATE_CERTS = config.getboolean("email", "VALIDATE_CERTS")
    MAIL_USERNAME = config.get("email", "MAIL_USERNAME")
    MAIL_PASSWORD = config.get("email", "MAIL_PASSWORD")
    MAIL_SUBJECT_PREFIX = "[Procurement App]"
    MAIL_FROM = "Procurement Admin <procurement@example.com>"


origins = config.get("origins", "ORIGINS")
mail_config = MailConfig()
settings = AppSettings()
