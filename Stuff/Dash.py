from User import User
from Suggestions import Suggestions
from Restaurant import Restaurant
from terminaltables import AsciiTable
import requests
from Order import Order
from Item import Item
import sys
from docopt import docopt
from geopy.geocoders import Nominatim

class CurrentItem(object):

	def __init__(self):
		super(CurrentItem, self).__init__()
		self.itemID = None
		self.quantity = None
		self.special_instructions = None
		self.substitution_preference = None


class Dash(object):
	
	def __init__(self):
		super(Dash, self).__init__()
		self.authorizationToken = None
		self.suggestionObject = None
		self.restaurantID = None
		self.currentSuggestion = None
		self.currentItem = CurrentItem()
		self.currentLocation = None

	def beginDashing(self, username, password):
		userObject = User()
		userObject.authenticate(username, password)
		self.authorizationToken = userObject.authorizationToken
		if self.authorizationToken != None:
			geolocator = Nominatim()
			location = self.promptUserWithMessage("Please enter a location: ")
			self.currentLocation = geolocator.geocode(location)
			if self.currentLocation != None:
				self.findSuggestions()
			else:
				print "Could not find information for the entered location."

	def findSuggestions(self):
		self.suggestionObject = Suggestions(self.authorizationToken, self.currentLocation)
		choices = self.suggestionObject.retrieveSuggestions()
		self.listSuggestions(choices)
		user_selection = self.promptUserWithMessage("Enter the number corresponding to what'll like to order: ")
		isSelectionValid = self.validateUserSelectionWithRange(user_selection, 1, len(choices))
		if isSelectionValid == True:
			self.currentSuggestion = choices[int(user_selection)-1]
			self.findRestaurantsForSuggestion(self.currentSuggestion)
		else:
			print "Please enter a valid number between 1 and "+str(len(choices))

	def promptUserWithMessage(self, message):
		return raw_input(message)

	def validateUserSelectionWithRange(self, selection, startRange, endRange):
		isSelectionValid = True

		if str(selection) == 'q':
			sys.exit(1)

		if selection.isdigit() == False:
			return

		if int(selection) < startRange or int(selection) > endRange:
			print selection, startRange, endRange
			isSelectionValid = False

		return isSelectionValid

	def listSuggestions(self,choices):
		headerArray = ["No", "What you'll like to order."]
		suggestionArray = []
		suggestionArray.append(headerArray)
		for index, choice in enumerate(choices):
			choiceArray = []
			choiceArray.append(index+1)
			choiceArray.append(choice)
			suggestionArray.append(choiceArray)
		table = AsciiTable(suggestionArray)
		print table.table

	def findRestaurantsForSuggestion(self, suggestion):
		restaurantsList = self.suggestionObject.listOfRestaurantsForSuggestion(suggestion)
		restaurantIDs = self.listRestaurants(restaurantsList)
		user_restaurantSelection = self.promptUserWithMessage("Select a restaurant number to see the menu: ")
		self.validateUserSelectionWithRange(user_restaurantSelection, 1, len(restaurantIDs))
		self.restaurantID = restaurantIDs[int(user_restaurantSelection)-1]
		self.fetchMenuForRestaurant(restaurantIDs[int(user_restaurantSelection)-1])

	def fetchMenuForRestaurant(self, restaurantID):
		restaurantObject = Restaurant(restaurantID,self.authorizationToken)
		data = restaurantObject.getMenuAndOtherRestaurantDetails()
		self.listMenuForSelectedRestaurant(data)	

	def listRestaurants(self,data):

			resultArray = []
			headerArray = ["No","Name", "Description", "Address", "Delivery Fees", "Rating", "Price Range", "Promotion"]
			restaurantIDs = []
			resultArray.append(headerArray)
			restaurantNumber = 0

			for restaurant in data:
				restaurantDetails = []
				restaurantNumber+=1
				restaurantDetails.append(str(restaurantNumber))
				restaurantDetails.append(restaurant["name"])
				restaurantDetails.append(restaurant["description"])
				restaurantDetails.append(restaurant["address"]["city"])
				restaurantDetails.append(str(restaurant["delivery_fee"]/100.0) )
				restaurantDetails.append(restaurant["composite_score"])
				restaurantDetails.append(self.getDollarRepresentationForPriceRange(restaurant["price_range"]))
				restaurantDetails.append(restaurant["promotion"])
				restaurantIDs.append(restaurant["id"])
				resultArray.append(restaurantDetails)

			table = AsciiTable(resultArray)
			print table.table
			return restaurantIDs

	def getDollarRepresentationForPriceRange(self,range):
		if int(range) == 1:
			return "$"
		elif int(range) == 2:
			return "$$"
		elif int(range) == 3:
			return "$$$"
		else:
			return "$$$$"

	def listMenuForSelectedRestaurant(self,data):
		headerArray = ["Number","Name", "Title","Price"]
		itemArray = []
		itemArray.append(headerArray)
		itemNumber = 0
		itemID = []

		if data[0].get('status') == "Closed":
			print "The restaurant you have selected is currently closed. :("
			self.findRestaurantsForSuggestion(self.currentSuggestion)
			return
		
		for category in data[0].get("menu_categories"): 
			items = category["items"]

			for item in items:
				detailArray = []
				itemNumber+=1
				itemID.append(item["id"])
				detailArray.append(str(itemNumber))
				detailArray.append(item["name"])
				detailArray.append(category["title"])
				detailArray.append(str(item["price"]/100.0))
				itemArray.append(detailArray)

		table = AsciiTable(itemArray)
		print table.table

		user_selection = self.promptUserWithMessage("You can add an item to the cart by entering a number or pressing q to quit: ")

		self.addItem(user_selection, itemArray, itemID)

	def addItem(self, user_selection, itemArray, itemID):
		if self.validateUserSelectionWithRange(user_selection, 1, len(itemArray)) == False:
			return

		if user_selection == "q":
			sys.exit(1)
		else:
			self.currentItem.quantity = self.promptUserWithMessage("How many quantities of the item would you like? ")

			if self.currentItem.quantity.isdigit() == False:
				print "Quantity entered should be a number."
				return

			self.currentItem.special_instructions = self.promptUserWithMessage("If you have any special instructions, mention here or press s to skip: ")
			if self.currentItem.special_instructions == "s":
				self.currentItem.special_instructions = ""

			resultArray = []
			headerArray = ["Number", "Substitution Preference"]
			substitutionChoices = ["Contact me", "Go with Merchant Recommendation", "Refund this item", "Cancel the entire order"]
			resultArray.append(headerArray)
			for index, choice in enumerate(substitutionChoices):
					choiceArray = []
					choiceArray.append(index+1)
					choiceArray.append(choice)
					resultArray.append(choiceArray)

			table = AsciiTable(resultArray)
			print table.table

			substitution_preference = self.promptUserWithMessage("If the item is sold out, what's your prefence. Choose a number from the table above: ")

			if self.validateUserSelectionWithRange(substitution_preference, 1, 4) == False:
				print "Please select a valid number according to the table."
				return

			if int(substitution_preference) == 1:
				self.currentItem.substitution_preference = "contact"
			elif int(substitution_preference) == 2:
				self.currentItem.substitution_preference = "substitute"
			elif int(substitution_preference) == 2:
				self.currentItem.substitution_preference = "refund"
			else:
				self.currentItem.substitution_preference = "cancel"

			self.currentItem.itemID = itemID[int(user_selection) - 1]
			self.getOptionsForItem()

	def getOptionsForItem(self):

		print "Getting options for the selected item"

		itemObject = Item(self.authorizationToken)
		itemDetails = itemObject.getItemOptions(self.restaurantID, self.currentItem.itemID)
		self.listOptionsForItem(itemDetails)


	
	def listOptionsForItem(self, data):

		if not data.get('extras'):
			self.addOrderToCart([])
			return

		options = data.get('extras')

		tableArray = []
		headerArray = ["Number", "Title", "Type", "Description", "Price", "Optional"]
		tableArray.append(headerArray)
		choiceID = []
		minimum_options = 0

		index = 0

		if options:
			for option in options:
				for choice in option["options"]:
					optionArray = []
					choiceID.append(choice["id"])
					index+=1
					optionArray.append(index)
					optionArray.append(option["title"])
					optionArray.append(choice["name"])
					optionArray.append(choice["description"])
					optionArray.append(str(choice["price"] / 100.0))
					minimum_options = option["min_num_options"]
					if int(minimum_options) == 0:
						optionArray.append("Yes")
					else:
						optionArray.append("No")
					tableArray.append(optionArray)
				minimum_options = option["min_num_options"]

		table = AsciiTable(tableArray)
		print table.table

		if minimum_options == 1:
			choice_selection = self.promptUserWithMessage("You need to select a minimum of one option to proceed forward: ")
			choice_selection_list = choice_selection.split(",")
			self.addChoiceIDs(choice_selection_list, choiceID)

		else:
			choice_selection = self.promptUserWithMessage("You can add options or enter p to proceed: ")
			if choice_selection == "p":
				self.addOrderToCart([])
			else:
				choice_selection_list = choice_selection.split(",")
				self.addChoiceIDs(choice_selection_list, choiceID)

	def addChoiceIDs(self,choice_selection_list, choiceID):
		orderArray = []
		for choice in choice_selection_list:
			choice = choice.strip()
			if self.validateUserSelectionWithRange(choice, 1, len(choiceID)) == False:
				print "Enter a valid selection."
				return
			orderArray.append(choiceID[int(choice) - 1])
		self.addOrderToCart(orderArray)

	def addOrderToCart(self, options):

		orderObject = Order(self.authorizationToken)
		orderObject.addItemToOrder(self.restaurantID, self.currentItem.itemID,options, self.currentItem.quantity, self.currentItem.special_instructions, self.currentItem.substitution_preference)
		data = orderObject.currentCart()
		self.showTheCurrentCart(data)

	def showTheCurrentCart(self, data):

		print "Your current cart is shown below:"
		tableData = []
		headerArray = ["No" ,"Item Name", "Quantity", "Special Instructions", "Price"]
		tableData.append(headerArray)

		items = data["orders"][0].get("order_items")

		for item in items:
			itemDetails = item["item"]
			index = 0
			itemData = []
			itemData.append(index+1)
			itemData.append(itemDetails["name"])
			itemData.append(item["quantity"])
			itemData.append(item["special_instructions"])
			itemData.append(int(item["single_price"]) /100.0)
			tableData.append(itemData)
			
		table = AsciiTable(tableData)
		print table.table

		print "Enter 1 for checking out the menu of the current restaurant"
		print "Enter 2 for finding restaurants for your current suggestions"
		print "Enter 3 for looking at the list of suggestions"


		next_step = self.promptUserWithMessage("What do you want to do next? : ")

		if self.validateUserSelectionWithRange(next_step, 1, 3) == True:
			
			if int(next_step) == 1:
				self.fetchMenuForRestaurant(self.restaurantID)
			elif int(next_step) == 2:
				self.findRestaurantsForSuggestion(self.currentSuggestion)
			else:
				self.findSuggestions()

def main():
	if len(sys.argv) <= 2:
		print "Please enter your username and password seperated by space."
		return

	dashObject = Dash()
	dashObject.beginDashing(str(sys.argv[1]), str(sys.argv[2]))

main()
			