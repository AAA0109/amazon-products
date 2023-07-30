from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ServingStatusDetails(BaseModel):
    detail_name: Optional[str] = Field(alias="name")
    help_url: Optional[str] = Field(alias="helpUrl")
    message: Optional[str]


class ExtendedData(BaseModel):
    last_update_date_time: Optional[datetime] = Field(alias="lastUpdateDateTime")
    serving_status: Optional[str] = Field(alias="servingStatus")
    serving_status_details: Optional[list[ServingStatusDetails]] = Field(
        alias="servingStatusDetails"
    )
    creation_date_time: Optional[datetime] = Field(alias="creationDateTime")

    class Config:
        allow_population_by_field_name = True
