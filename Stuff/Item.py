import requests
import constants
import json
import sys

class Item(object):
	"""docstring for Item"""
	def __init__(self, authorizationToken):
		super (Item, self).__init__()
		self.authorizationToken = authorizationToken

	def getItemOptions(self,restaurantID, itemID):

		headers = {'authorization': self.authorizationToken}
		url = constants.itemDetailsURL + str(restaurantID) + "/item/" + str(itemID) + "/"
		try:
			response = requests.request("GET", url, headers= headers)
		except Exception, e:
			print e.cause
			sys.exit(1)
		
		data = json.loads(response.text)
		return data

	def deleteItemFromCart(self, userID, itemID):

		url = "https://api.doordash.com/v2/consumer/"+str(userID)+"/order/current_order/item/" + str(itemID)

		headers = {
    	'content-type': "application/json",
   		'authorization': self.authorizationToken
    	}
	
		response = requests.request("DELETE", url, data=payload, headers=headers)

		data = json.loads(response.text)
		return data
