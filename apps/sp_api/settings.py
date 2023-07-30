import os

from dotenv import load_dotenv

load_dotenv("../.env.dev")

SP_API_CLIENT_ID = os.getenv("SP_API_CLIENT_ID", "")
SP_API_CLIENT_SECRET = os.getenv("SP_API_CLIENT_SECRET", "")
SP_API_REFRESH_TOKEN_NA = os.getenv("SP_API_REFRESH_TOKEN_NA", "")
SP_API_REFRESH_TOKEN_EU = os.getenv("SP_API_REFRESH_TOKEN_EU", "")
SP_API_REFRESH_TOKEN_FE = os.getenv("SP_API_REFRESH_TOKEN_AU", "")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY", "")
APP_ID = os.getenv("APP_ID", "")
AWS_SECRET_KEY: str = os.getenv("AWS_SECRET_KEY", "")
SP_API_SERVICE_NAME: str = os.getenv("SP_API_SERVICE_NAME", "")
ROLE_ARN = os.getenv("ROLE_ARN", "")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "parazun-amazon-data.p.rapidapi.com")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
