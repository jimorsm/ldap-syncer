'''
Created by auto_sdk on 2021.01.20
'''
from dingtalk.api.base import RestApi
class OapiAuthorizationRbacPermissionGetRequest(RestApi):
	def __init__(self,url=None):
		RestApi.__init__(self,url)
		self.agent_id = None
		self.resource = None
		self.userid = None

	def getHttpMethod(self):
		return 'POST'

	def getapiname(self):
		return 'dingtalk.oapi.authorization.rbac.permission.get'
