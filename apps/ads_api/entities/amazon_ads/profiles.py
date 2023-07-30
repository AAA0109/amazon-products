from typing import Optional, Iterator

from pydantic import BaseModel, Field, validator


class AccountInfoEntity(BaseModel):
    marketplace_id: str = Field(alias="marketplaceStringId")
    sub_type: Optional[str] = Field(alias="subType")
    valid_payment_method: bool = Field(alias="validPaymentMethod")
    id: str
    type: str
    name: str


class ProfileEntity(BaseModel):
    profile_id: int = Field(alias="profileId")
    country_code: str = Field(alias="countryCode")
    currency_code: str = Field(alias="currencyCode")
    account_info: Optional[AccountInfoEntity] = Field(alias="accountInfo")
    timezone: str

    @validator("country_code")
    def country_code_to_upper(cls, v: str):
        return v.upper()


class ProfilesListEntity(BaseModel):
    __root__: list[ProfileEntity]

    def __iter__(self) -> Iterator[ProfileEntity]:
        return iter(self.__root__)

    def __getitem__(self, item) -> ProfileEntity:
        return self.__root__[item]

    @property
    def ids(self) -> list[int]:
        return [p.profile_id for p in self.__root__]
