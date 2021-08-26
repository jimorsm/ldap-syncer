'''
Created by auto_sdk on 2021.06.10
'''
from dingtalk.api.base import RestApi
class OapiAttendanceGroupModifyRequest(RestApi):
	def __init__(self,url=None):
		RestApi.__init__(self,url)
		self.op_user_id = None
		self.top_group = None

	def getHttpMethod(self):
		return 'POST'

	def getapiname(self):
		return 'dingtalk.oapi.attendance.group.modify'
