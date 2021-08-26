import logging
import time
from typing import Dict, List, Optional

from dingtalk import api as dingtalk_api
from pydantic import BaseModel

from .schemas import DeptInDingtalk as Dept, UserInDingtalk as User


class Provider:
    def __init__(self, type: Optional[str] = None) -> None:
        self.type = None


class Dingding(Provider):
    """
    通过钉钉接口获取、操作用户与组织关系数据"""

    def __init__(self, appkey: str, appsecret: str) -> None:
        self.appkey = appkey
        self.appsecret = appsecret
        self.__token_cache: Optional(Dict) = None
        logging.debug(
            "provider dingding initialized, appkey: {}, appsecret: {}".format(
                appkey, appsecret
            )
        )

    @property
    def access_token(self) -> str:
        if self.__token_cache:
            if self.__token_cache.get("expire_time") > time.time():
                return self.__token_cache.get("access_token")
        req = dingtalk_api.OapiGettokenRequest("https://oapi.dingtalk.com/gettoken")
        req.appkey = self.appkey
        req.appsecret = self.appsecret
        try:
            resp = req.getResponse()
            resp["expire_time"] = time.time() + resp.get("expires_in")
            self.__token_cache = resp
            logging.debug(
                "provider dingding get and cached new token: {}, expire time: {}.".format(
                    resp["access_token"],
                    time.asctime(time.localtime(resp["expire_time"])),
                )
            )
            return resp.get("access_token")
        except Exception as e:
            print(e)

    def get_sub_dept_list(self, parent_dept_id: int = 1) -> List[Dept]:
        """获取子部门列表"""
        req = dingtalk_api.OapiV2DepartmentListsubRequest(
            "https://oapi.dingtalk.com/topapi/v2/department/listsub"
        )
        req.dept_id = parent_dept_id
        try:
            resp = req.getResponse(self.access_token)
            sub_dept_list = [Dept.parse_obj(i) for i in resp.get("result")]
            logging.debug(
                "provider dingding get sub dept list of dept_id {}, sub dept lsit: {}.".format(
                    parent_dept_id, sub_dept_list
                )
            )
            return sub_dept_list

        except Exception as e:
            logging.error("provider dingding error: {}.".format(e))

        #     [
        #            {
        #                 "sourceIdentifier": "111",
        #                 "createDeptGroup": false,
        #                 "name": "财务部",
        #                 "id": 420727358,
        #                 "autoAddUser": false,
        #                 "parentid": 1
        #         },
        #         {
        #                 "createDeptGroup": false,
        #                 "name": "研发",
        #                 "id": 411048776,
        #                 "autoAddUser": false,
        #                 "parentid": 1
        #         }
        # ]

    def get_dept_list(self, parent_dept_id: int = 1) -> List[Dept]:
        """递归获取所有部门"""
        dept_list = [self.get_dept_detail(dep_id=parent_dept_id)]
        for dept in self.get_sub_dept_list(parent_dept_id=parent_dept_id):
            sub_list = self.get_dept_list(parent_dept_id=dept.dept_id)
            if sub_list:
                dept_list.extend(sub_list)
        return dept_list

    def get_dept_detail(self, dep_id: int = 1) -> Dept:
        """获取部门详情"""
        req = dingtalk_api.OapiV2DepartmentGetRequest(
            "https://oapi.dingtalk.com/topapi/v2/department/get"
        )
        req.dept_id = dep_id
        try:
            resp = req.getResponse(self.access_token)
            return Dept.parse_obj(resp.get("result"))
        except Exception as e:
            logging.error("provider dingding error: {}.".format(e))

    def get_dept_userid_list(self, dept_id: int = 1) -> List:
        req = dingtalk_api.OapiUserListidRequest(
            "https://oapi.dingtalk.com/topapi/user/listid"
        )
        req.dept_id = dept_id
        try:
            resp = req.getResponse(self.access_token)
            return resp.get("result").get("userid_list")
        except Exception as e:
            logging.error("provider dingding error: {}.".format(e))

        # [
        #     "usxxx",
        #     "manager4xxx",
        #     "10203029011xxxx",
        #     "usexxx"
        # ]

    def get_dept_user_list(
        self, dept_id: int = 1, cursor: int = 0, size: int = 50
    ) -> List[User]:
        user_list = []
        while True:
            req = dingtalk_api.OapiV2UserListRequest(
                "https://oapi.dingtalk.com/topapi/v2/user/list"
            )
            req.dept_id = dept_id
            req.cursor = cursor
            req.size = size
            try:
                resp = req.getResponse(self.access_token)
                user_list.extend(
                    [User.parse_obj(user) for user in resp["result"]["list"]]
                )
                if resp["result"]["has_more"]:
                    cursor = resp["next_cursor"]
                else:
                    break
            except Exception as e:
                logging.error("provider dingding error: {}.".format(e))
                break
        logging.debug(
            "provider dingding: get user list of dept_id {}, user list: {}.".format(
                dept_id, user_list
            )
        )
        return user_list

        # [
        #     {
        #         "dept_order": 1,
        #         "leader": "true",
        #         "extension": "{\"爱好\":\"旅游\",\"年龄\":\"24\"}",
        #         "unionid": "z21HjQlxxxx",
        #         "boss": "true",
        #         "exclusive_account": "false",
        #         "mobile": "18513027676",
        #         "active": "true",
        #         "admin": "true",
        #         "telephone": "010-86123456-2345",
        #         "remark": "备注备注",
        #         "avatar": "xxx",
        #         "hide_mobile": "false",
        #         "title": "技术总监",
        #         "hired_date": "1597573616828",
        #         "userid": "zhangsan",
        #         "work_place": "未来park",
        #         "org_email": "test@xxx.com",
        #         "name": "张三",
        #         "dept_id_list": [
        #             2,
        #             3,
        #             4
        #         ],
        #         "job_number": "4",
        #         "state_code": "86",
        #         "email": "test@xxx.com"
        #     }
        # ]

    def get_user_all(self) -> List[User]:
        user_list = [
            user
            for dept in self.get_dept_list()
            for user in self.get_dept_user_list(dept.dept_id)
        ]
        logging.debug("provider dingding: get all user list {}.".format(user_list))
        return user_list

    def get_user_detail(self, user_id: int) -> Dict:
        req = dingtalk_api.OapiV2UserGetRequest(
            "https://oapi.dingtalk.com/topapi/v2/user/get"
        )
        req.userid = user_id
        try:
            resp = req.getResponse(self.access_token)
            return resp.get("userid_list")
        except Exception as e:
            logging.error("provider dingding error: {}.".format(e))

        # {
        #     "extension": '{"爱好":"旅游","年龄":"24"}',
        #     "unionid": "xBnhjgjmofhhsLxxx",
        #     "boss": false,
        #     "unionEmpExt": {
        #         "corpId": "ding1c417cfd9e3142d1acaaa37764f9xxxx",
        #         "userid": "45694432-1019596262",
        #         "unionEmpMapList": [
        #             {
        #                 "corpId": "ding1c417cfd9e3142d1acaaa37764f9xxxx",
        #                 "userid": "45694432-1019596262",
        #             }
        #         ],
        #     },
        #     "role_list": [{"group_name": "默认", "id": 1507113578, "name": "主管理员"}],
        #     "admin": true,
        #     "remark": "杨XX",
        #     "title": "服务经理",
        #     "hired_date": 1598457600000,
        #     "userid": "manager4220",
        #     "work_place": "杭州",
        #     "dept_order_list": [
        #         {"dept_id": 1, "order": 176318669012199520},
        #         {"dept_id": 379661095, "order": 176318556766960500},
        #     ],
        #     "real_authed": true,
        #     "dept_id_list": [1, 379661095],
        #     "job_number": "10001",
        #     "email": "1@example.com",
        #     "leader_in_dept": [
        #         {"dept_id": 379661095, "leader": false},
        #         {"dept_id": 1, "leader": false},
        #     ],
        #     "manager_userid": "user01",
        #     "mobile": "188xxxx1234",
        #     "active": true,
        #     "telephone": "010-8xxxx6-2345",
        #     "avatar": "",
        #     "hide_mobile": false,
        #     "senior": false,
        #     "name": "杨xxx",
        #     "state_code": "86",
        # }
