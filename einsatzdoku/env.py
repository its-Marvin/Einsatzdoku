import os
import random, string

def randomword(length):
   letters = string.ascii_lowercase + string.ascii_uppercase
   return ''.join(random.choice(letters) for i in range(length))

def invalid_configuration(key):
    print(f"Missing value for config key {key}! Terminating...")
    exit(1)


DJANGO_SECRET = os.environ.get("DJANGO_SECRET")
if DJANGO_SECRET is None: invalid_configuration("DJANGO_SECRET")
DJANGO_DEBUG = True if os.environ.get("DJANGO_DEBUG", "False") == "True" else False
DB_TYPE = os.environ.get("DB_TYPE", "SQLite")
if DB_TYPE == "POSTGRES":
    DB_HOST = os.environ.get("DB_HOST")
    DB_PORT = os.environ.get("DB_PORT", 5432)
    DB_USER = os.environ.get("DB_USER")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")
    DB_NAME = os.environ.get("DB_NAME")
    # Check that required variables are set
    if DB_HOST is None: invalid_configuration("DB_HOST")
    if DB_NAME is None: invalid_configuration("DB_NAME")
    if DB_USER is None: invalid_configuration("DB_USER")
    if DB_PASSWORD is None: invalid_configuration("DB_PASSWORD")
