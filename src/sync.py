from utils import Dingding, Driver, Ldap, Provider, Paser
from config import setting


class Syncer:
    def __init__(self, provider: Provider, driver: Driver) -> None:
        self.driver = driver
        self.provider = provider
        self.pase = Paser("dd")

    def pull_dept(self):
        """从provider获取部门并创建ou"""
        for p_dept in provider.get_dept_list():
            l_dept = self.pase(p_dept)
            self.driver.create_dept(l_dept)

    def pull_user(self):
        """从provider获取用户并创建cn"""
        # 遍历部门用户
        for p_user in provider.get_user_all():
            l_user = self.pase(p_user)
            # 创建用户
            self.driver.create_user(user=l_user)


if __name__ == "__main__":
    provider = Dingding(
        appkey=setting.DINGDING_APPKEY, appsecret=setting.DINGDING_APPSECRET
    )
    driver = Ldap(
        server=setting.LDAP_SERVER,
        user=setting.LDAP_ADMIN,
        password=setting.LDAP_ADMIN_PASSWD,
    )

    syncer = Syncer(provider=provider, driver=driver)
    syncer.pull_dept()
    syncer.pull_user()
