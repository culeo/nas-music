from pydantic import BaseModel, Field, field_validator

class UserBase(BaseModel):
    username: str
    realName: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    realName: str = None
    password: str = None


class UserInDB(UserBase):
    id: int
    preferences: dict[str, str] = Field(default_factory=dict)  # 定义为字典

    @field_validator("preferences", mode="before")
    def convert_preferences_to_dict(cls, value):
        if isinstance(value, list):  # 如果是列表，进行转换
            return {pref.key: pref.value for pref in value}
        return value

    class Config:
        from_attributes = True
