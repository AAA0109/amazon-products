import enum

from apps.ads_api.constants import ServerLocation
from apps.sp_api import settings

credentials = {
    ServerLocation.NORTH_AMERICA: dict(
        refresh_token=settings.SP_API_REFRESH_TOKEN_NA,
        lwa_app_id=settings.SP_API_CLIENT_ID,
        lwa_client_secret=settings.SP_API_CLIENT_SECRET,
        aws_access_key=settings.AWS_ACCESS_KEY,
        aws_secret_key=settings.AWS_SECRET_KEY,
    ),
    ServerLocation.EUROPE: dict(
        refresh_token=settings.SP_API_REFRESH_TOKEN_EU,
        lwa_app_id=settings.SP_API_CLIENT_ID,
        lwa_client_secret=settings.SP_API_CLIENT_SECRET,
        aws_access_key=settings.AWS_ACCESS_KEY,
        aws_secret_key=settings.AWS_SECRET_KEY,
    ),
    ServerLocation.FAR_EAST: dict(
        refresh_token=settings.SP_API_REFRESH_TOKEN_FE,
        lwa_app_id=settings.SP_API_CLIENT_ID,
        lwa_client_secret=settings.SP_API_CLIENT_SECRET,
        aws_access_key=settings.AWS_ACCESS_KEY,
        aws_secret_key=settings.AWS_SECRET_KEY,
    ),
}
