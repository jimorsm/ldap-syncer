from typing import Union
from .schemas import User, UserInDingtalk, UserInLdap, Dept, DeptInDingtalk, DeptInLdap
from pydantic import BaseModel

"""
负责钉钉数据与ldap数据之间得互相转换
"""


class Paser:
    def __init__(self, prefix: str) -> None:
        self.prefix = prefix + "_"
        self.prefix_len = len(self.prefix)

    def convert_id(self, id: str):
        id = str(id)
        if id.startswith(self.prefix):
            return id[self.prefix_len - 1 :]
        elif id == "1":
            return "1"
        else:
            return self.prefix + id

    def provider2ldap(self, obj: Union[UserInDingtalk, DeptInDingtalk]):
        obj_d = obj.dict()
        for attr in ["dept_id", "parent_id", "userid", "dept_id_list"]:
            if hasattr(obj, attr) and getattr(obj, attr):
                value = getattr(obj, attr)
                if isinstance(value, list):
                    obj_d[attr] = [self.convert_id(i) for i in value]
                else:
                    obj_d[attr] = self.convert_id(value)

        if isinstance(obj, UserInDingtalk):
            return UserInLdap(**obj_d)
        elif isinstance(obj, DeptInDingtalk):
            return DeptInLdap(**obj_d)

    def ldap2provider(self, obj: Union[UserInLdap, DeptInLdap]):
        obj_d = obj.dict()
        for attr in ["departmentNumber", "uniqueIdentifier"]:
            if hasattr(obj, attr) and getattr(obj, attr):
                v = None
                for id in getattr(obj, attr):
                    if id.startswith(self.prefix):
                        v = self.convert_id(id)
                obj_d[attr] = v

        if isinstance(obj, UserInLdap):
            return UserInLdap(**obj_d)
        elif isinstance(obj, DeptInLdap):
            return DeptInLdap(**obj_d)

    def parse(self, obj: BaseModel):
        if isinstance(obj, UserInDingtalk) or isinstance(obj, DeptInDingtalk):
            return self.provider2ldap(obj)
        elif isinstance(obj, UserInLdap) or isinstance(obj, DeptInLdap):
            return self.ldap2provider(dept=obj)

    def __call__(
        self, obj: Union[UserInLdap, UserInDingtalk, DeptInDingtalk, DeptInLdap]
    ):
        return self.parse(obj)
