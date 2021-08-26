from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, Union
from pydantic.fields import Field

"""
driver 与 provider 中获取到数据得 schema
"""


class User(BaseModel):
    pass


class UserInDingtalk(User):
    # TODO: UserInLdap -> UserInDingtalk 数据转换
    email: Optional[EmailStr] = None
    mobile: int
    title: Optional[str] = None
    userid: Optional[Union[str, list]] = Field(..., alias="uniqueIdentifier")
    name: str
    dept_id_list: Optional[Union[int, List[int]]] = None
    job_number: Optional[int] = None

    @validator("userid")
    def value_convert(cls, v) -> str:
        if isinstance(v, list):
            for i in v:
                if i.startwith("dd_"):
                    return i
        return v

    class Config:
        allow_population_by_field_name = True


class UserInLdap(User):
    email: Optional[EmailStr] = None
    mobile: int
    title: Optional[str] = None
    uniqueIdentifier: Union[str, List[str]] = Field(..., alias="userid")
    cn: str = Field(..., alias="name")
    departmentNumber: Optional[Union[int, List]] = Field(None, alias="dept_id_list")
    employeeNumber: Optional[int] = Field(None, alias="job_number")

    @validator("uniqueIdentifier", "departmentNumber")
    def value_convert(cls, v) -> List[str]:
        if isinstance(v, str):
            return [v]
        return v

    class Config:
        allow_population_by_field_name = True


class Dept(BaseModel):
    pass


class DeptInDingtalk(Dept):
    dept_id: str
    name: Optional[str]
    parent_id: Optional[int] = None


class DeptInLdap(Dept):
    departmentNumber: Union[str, List[str]] = Field(..., alias="dept_id")
    ou: Optional[str] = Field(None, alias="name")
    parent_id: Optional[str] = None

    @validator("departmentNumber")
    def value_convert(cls, v) -> List[str]:
        if isinstance(v, str):
            return [v]
        return v

    class Config:
        allow_population_by_field_name = True
