import logging
from typing import Dict, List, Optional, Union

from ldap3 import (
    ALL,
    HASHED_SALTED_SHA,
    HASHED_SHA,
    MODIFY_ADD,
    MODIFY_REPLACE,
    AttrDef,
    Connection,
    Entry,
    ObjectDef,
    Reader,
    Server,
    Writer,
)
from ldap3.utils.hashed import hashed
from pypinyin import NORMAL, pinyin

from .schemas import DeptInLdap as Dept
from .schemas import UserInLdap as User

"""
操作ldap服务器数据
"""


class NameTools:
    @staticmethod
    def is_all_chinese(strs):
        for _char in strs:
            if not "\u4e00" <= _char <= "\u9fa5":
                return False
        return True

    @staticmethod
    def get_name_pinyin(name: str):
        if NameTools.is_all_chinese(name):
            return "".join([i[0] for i in pinyin(name, style=NORMAL)])
        raise Exception("Not Chinese")

    @staticmethod
    def get_surname(name: str):
        if NameTools.is_all_chinese(name):
            if len(name) < 4:
                return name[0]
            else:
                return name[0:2]
        raise Exception("Not Chinese")


class Driver:
    def __init__(self, *args, **kwargs) -> None:
        self.type = None

    def create_dept(self):
        pass

    def search_dept(self):
        pass

    def create_user(self):
        pass

    def search_user(self):
        pass


# server = Server('ldap://156.234.201.236',get_info=ALL)
# conn = Connection(server=server, user='cn=admin,dc=example,dc=org',password='adminpassword',auto_bind=True)
class Ldap(Driver):
    def __init__(
        self,
        server: str,
        user: str,
        password: str,
        base_dn: str = "dc=example,dc=org",
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.type = "ldap"
        self.server = Server(server, get_info=ALL)
        self.conn = Connection(
            server=self.server, user=user, password=password, auto_bind=True
        )
        self.base_dn = base_dn
        self.base_ou_object_class = ["organizationalUnit", "top", "extensibleObject"]
        self.base_ou_object_def = ObjectDef(
            object_class=self.base_ou_object_class, schema=self.conn
        )
        self.base_ou = {
            "user": {
                "sub_item_object_class": [
                    "top",
                    "person",
                    "organizationalPerson",
                    "inetOrgPerson",
                    "extensibleObject",
                ],
                "sub_item_extra_attr": [],
            },
            "dept": {
                "sub_item_object_class": [
                    "top",
                    "organizationalUnit",
                    "extensibleObject",
                ],
                "sub_item_extra_attr": [{"attr": "departmentNumber", "value": "1"}],
            },
            "group": {"sub_item_object_class": [], "sub_item_extra_attr": []},
        }

        self.__create_base_ou()

    def __create_base_ou(self):
        for base_ou_name, sub_item_conf in self.base_ou.items():

            # set base ou dn
            dn = "ou={},{}".format(base_ou_name, self.base_dn)
            setattr(
                self,
                "{}_base_dn".format(base_ou_name),
                dn,
            )

            # set base ou sub item object class
            object_class = sub_item_conf["sub_item_object_class"]
            setattr(
                self,
                "{}_object_class".format(base_ou_name),
                object_class,
            )

            # set base ou sub item object def
            obj_def = ObjectDef(sub_item_conf["sub_item_object_class"], self.conn)
            for extra_attr in sub_item_conf["sub_item_extra_attr"]:
                obj_def += extra_attr["attr"]
            setattr(
                self,
                "{}_object_def".format(base_ou_name),
                obj_def,
            )

            if not self.search_entry(
                object_def=self.base_ou_object_def,
                base=self.base_dn,
                query="(ou={})".format(base_ou_name),
            ):
                attributes = {}
                for item in sub_item_conf["sub_item_extra_attr"]:
                    attributes[item["attr"]] = item["value"]
                self.create_entry(
                    dn=dn, object_class=self.base_ou_object_class, attributes=attributes
                )

    def create_entry(
        self, dn: str, object_class: Union[str, List[str]], attributes: Dict = {}
    ) -> bool:
        result = False
        result = self.conn.add(
            dn=dn,
            object_class=object_class,
            attributes={k: v for k, v in attributes.items() if v},
        )
        logging.debug(
            "create entry {} with dn: {}, object_class: {}, attribuets: {}".format(
                "success" if result else "failed", dn, object_class, attributes
            )
        )
        return result

    def search_entry(
        self, object_def: ObjectDef, base: str, query: Optional[str] = ""
    ) -> List[Entry]:
        r = Reader(
            connection=self.conn,
            object_def=object_def,
            base=base,
            query=query,
        )
        try:
            result = r.search()
            logging.debug(
                "query:{}, result:{}".format(
                    query, [entry.entry_dn for entry in result]
                )
            )
            return result
        except Exception as e:
            logging.error("query:{}".format(query), e)
            return []

    def search_dept(
        self,
        dept: Optional[Dept] = None,
        dept_id: Optional[Union[str, list]] = None,
        dept_name: Optional[str] = None,
        policy="any",
    ) -> List[Entry]:

        if not (dept or dept_id or dept_name):
            raise TypeError(
                "search_dept() required argument: dept or dept_id or dept_name"
            )

        if dept:
            dept_id_list = dept.departmentNumber
            dept_name = dept.ou

        if dept_id:
            if isinstance(dept_id, list):
                dept_id_list = dept_id
            else:
                dept_id_list = [dept_id]

        s_tmp = ""
        for id in dept_id_list:
            s_tmp += "(departmentNumber={})".format(id)
        departmentNumber_query_str = "(|{})".format(s_tmp)

        ou_query_str = ""
        if dept_name:
            ou_query_str = "(ou={})".format(dept_name)

        if dept_id_list == ["1"]:
            policy = "any"

        if policy == "any":
            query_str = "(|{}{})".format(ou_query_str, departmentNumber_query_str)
        elif policy == "exact":
            query_str = "(&{}{})".format(ou_query_str, departmentNumber_query_str)
        return self.search_entry(
            object_def=self.dept_object_def, base=self.dept_base_dn, query=query_str
        )

    def create_dept(self, dept: Dept) -> bool:
        # TODO: 添加memberof属性

        msg = ""
        policy = "exact"
        if 1 in dept.departmentNumber:
            policy = "any"
        if self.search_dept(dept, policy=policy):
            result = False
            msg = "already exist"
        else:
            # get base dn
            parent_dn = self.dept_base_dn
            if dept.parent_id:
                parent_dept = self.search_dept(dept_id=dept.parent_id)
                if parent_dept:
                    parent_dn = parent_dept[0].entry_dn

            dn = "ou={},{}".format(dept.ou, parent_dn)
            attributes = dept.dict(exclude={"parent_id": ...})
            attributes["cn"] = dept.ou

            result = self.create_entry(
                dn=dn, object_class=self.dept_object_class, attributes=attributes
            )

        logging.debug(
            "create dept {} {} {}".format(
                dept.ou,
                "success" if result else "failed",
                ", reson: {}".format(msg) if msg else "",
            )
        )
        return result

    def search_user(self, user: User, policy="any"):
        query_list = []
        for k, v in user.dict(
            include={"uniqueIdentifier": ..., "cn": ..., "email": ..., "mobile": ...}
        ).items():
            query_str4_attr_k = ""
            if isinstance(v, list):
                list_tmp = []
                for i in v:
                    list_tmp.append("({}={})".format(k, i))
                query_str4_attr_k = "(|{})".format("".join(list_tmp))
            elif v:
                query_str4_attr_k = "({}={})".format(k, v)
            query_list.append(query_str4_attr_k)

        if policy == "any":
            query = "(|{})".format("".join(query_list))
        elif policy == "exact":
            query = "(&{})".format("".join(query_list))

        return self.search_entry(
            object_def=self.user_object_def, base=self.user_base_dn, query=query
        )

    def create_user(self, user: User):
        # TODO: POSIX 账号集成
        dn = "cn={},{}".format(user.cn, self.user_base_dn)
        attributes = user.dict(
            include={
                "uniqueIdentifier": ...,
                "cn": ...,
                "email": ...,
                "mobile": ...,
                "employeeNumber": ...,
                "title": ...,
                "departmentNumber": ...,
            }
        )
        attributes["sn"] = NameTools.get_surname(user.cn)
        if NameTools.is_all_chinese(user.cn):
            attributes["uid"] = NameTools.get_name_pinyin(user.cn)
        else:
            attributes["uid"] = user.cn

        msg = ""
        if self.search_user(user=user, policy="exact"):
            result = False
            msg = "already exist"
        else:
            defualt_passwd = (
                NameTools.get_name_pinyin(attributes["cn"])
                + str(attributes["mobile"])[-4:]
            )
            hashed_password = hashed(HASHED_SALTED_SHA, value=defualt_passwd)
            attributes["userPassword"] = hashed_password
            result = self.create_entry(
                dn=dn,
                object_class=self.user_object_class,
                attributes=attributes,
            )

        if result and user.departmentNumber:
            self.add_user2dept(user)

        logging.debug(
            "create user {} {} {}".format(
                user.cn,
                "success" if result else "failed",
                ", reson: {}".format(msg) if msg else "",
            )
        )
        return result

    def add_user2dept(self, user: User):
        for departmentNumber in user.departmentNumber:
            r_dept = self.search_dept(dept_id=departmentNumber, policy="exact")
            if r_dept:
                dept = r_dept[0]
                dn = dept.entry_dn
                user_dn = "cn=" + user.cn + "," + self.user_base_dn
                result = self.conn.modify(
                    dn=dept.entry_dn,
                    changes={"member": [(MODIFY_ADD, [user_dn])]},
                )
            logging.debug(
                "{} add member {} {}".format(
                    dn, user_dn, "success" if result else "failed"
                )
            )
