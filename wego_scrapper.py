from lxml import etree, html

import csv
import json
import os
import re
import sys
import urllib

class WeGoScrapper(object):

# To declare global variables
	def __init__(self):
		try:
			f = open('wego_countries.txt')
			self._countries = eval(f.read())
		except:
			self._countries = []
		try:
			f = open('wego_cities.txt')
			self._cities = eval(f.read())
		except:
			self._cities = []
		try:
			f = open('wego_hotels.txt')
			self._hotels = eval(f.read())
		except:
			self._hotels = []
		try:
			f = open('wego_hotels_details.txt')
			self._hotels_details = eval(f.read())
		except:
			self._hotels_details = []


# To print the output in a text file
	def save(self):
		print 'Saving'
		output = open('wego_countries.txt', 'w')
		output.write(str(self._countries))
		output.close()

		output = open('wego_cities.txt', 'w')
		output.write(str(self._cities))
		output.close()

		output = open('wego_hotels.txt', 'w')
		output.write(str(self._hotels))
		output.close()

		output = open('wego_hotels_details.txt', 'w')
		output.write(str(self._hotels_details))
		output.close()


# To get the url link and the page details
	def _get_tree_from_url(self, url):
		if not url:
			return
		if url.startswith('/'):
			url = "http://www.wego.co.in" + url
		urlstr = url.replace('/', '_')
		print "URL : " , url
		try:
			f = open("dump/%s" % urlstr, 'r')
			doc = html.fromstring(f.read())
			tree = etree.ElementTree(doc)
			print 'Found'
		except:
			print "Error:", sys.exc_info()[0]
			print 'Downloading'
			tree = html.parse(url)
			if not tree:
				print "\nFalling back"
				tree = html.parse(url)
			output = open("dump/%s" % urlstr, 'w')
			output.write(html.tostring(tree))
			output.close()
		return tree


# To parse the pages of specific hotel fo hotel detail
	def _parse_hotel_page(self, url , country_name , city_name , hotel_name):
		tree = self._get_tree_from_url(url)
		hotel_address = tree.findall("//div[@class='synopsis-adr']")

		city_list = []
		country_list = []
		hotel_list = []
		address_list = []
		low_price = []
		high_price = []
		no_of_stars = []
	
		link = ''
		for address in hotel_address:
			address_detail = address.findall("span")
# To get the address name
			for name in address_detail:
				link += name.text
				link += " , "

			city_list.append(city_name)
			country_list.append(country_name)
			hotel_list.append(hotel_name)
			address_list.append(link)

# To Get the low and high price of the hotel
		prices = tree.findall("//strong[@class='js-rate-price rate-price']")
		count = 0
		for price in prices:
			price_range = price.text
			if(count == 0):
				low_price.append(price.text)
			elif (count == 1):
				high_price.append(price.text)
			count+=1
			if (count == 2):
				break
		if (count == 1):
			high_price.append(" ")
		if (count == 0):
			high_price.append(" ")
			low_price.append(" ")

# To get the number of stars in the hotel name
		number_division = tree.findall("//span[@class='stars stars-details']")	
		for number in number_division:
			stars = number.findall("i[@class='icon-star']")
			count = 0
			for star in stars:
				count += 1
#		print "\nCountry Name : " , country_name
#		print "City Name : " , city_name
#		print "Hotel Name : " , hotel_name
#		print "Address : " , link
#		print "Number Of Stars : " , count
		no_of_stars.append(count)
		final = []
		final = zip (country_list , city_list , hotel_list , address_list , low_price , high_price , no_of_stars)
		self._hotels_details += final



# To parse the pages of city containing Hotel list to get hotel names and links
	def _parse_city_page(self, url , country_name , city_name):
		tree = self._get_tree_from_url(url)
		hotels = tree.findall("//a[@class='js-details-link']")
		city_list = []
		country_list = []
		hotel_list = []
		for hotel in hotels:
			link = hotel.get('href')
			city_list.append(city_name)
			hotel_list.append(hotel.text)
			country_list.append(country_name)
			self._parse_hotel_page(link , country_name , city_name , hotel.text)
		final = []
		final = zip (country_list , city_list , hotel_list)	
		self._hotels += final

		next_tags = tree.findall("//span[@class='next']")
		for next_tag in next_tags:
			next_tag_number = next_tag.findall("a")
			for name in next_tag_number:
				link = name.get('href')
				print "Link : " , link
				self._parse_city_page(link , country_name , city_name)


# To parse the pages for countries of Asia
	def _parse_country_page(self, url , country_name):
		tree = self._get_tree_from_url(url)
		cities = tree.findall("//li[@class='columns large-8 medium-8']")
		city_list = []
		country_list = []
		crap_city = ['assam']
		for city in cities:
			city_name = city.findall("a")
			for name in city_name:
				link = name.get('href')
				tuples = link.split('/')
				city_name = tuples[-1]
				city_list.append(city_name)
				country_list.append(country_name)
				if (city_name == 'pahalgam'):
					self.save()
					self.write_to_csv()
				self._parse_city_page(link , country_name , city_name)
		final = []
		final = zip (city_list , country_list)	
		self._cities += final

		next_tags = tree.findall("//span[@class='next']")
		for next_tag in next_tags:
			next_tag_number = next_tag.findall("a")
			for name in next_tag_number:
				link = name.get('href')
				print "Link : " , link
				self._parse_country_page(link , country_name)



# To parse the main page i.e www.wego.co.in/hotels/asia
	def _parse_directory_page(self, url):
		tree = self._get_tree_from_url(url)
		countries = tree.findall("//div[@class='country ']")
		country_list = []
		for country in countries:
			country_name = country.findall("a")
			for name in country_name:
				link = name.get('href')
				tuples = link.split('/')
				country_name = tuples[-1]
# Remove this line to get all countries
				if(country_name != 'india'):
					continue
				country_list.append(country_name)
				self._parse_country_page(link , country_name)
		self._countries += country_list


# As I want only the cities of asia
# I am directly scrapping from the asia link
# Uncomment all the lines to get hotel list of all world

	def get_countries(self):
		url = 'http://www.wego.co.in/hotels/asia'
		self._parse_directory_page(url)
		return self._countries

# To write to excel file the data
# wego_country.csv contains the country list
# wego_cities.csv contains the country list with corresponding city list
# wego_hotels.csv contains the country list with corresponding city list and hotel name + address
# wego_hotels_details.csv contains the Country + City + Hotel Name + Hotel Address + Low Price + High Price + Number Of Stars 

	def write_to_csv(self):
		with open('wego_country.csv', 'w') as c:
		  writer = csv.writer(c)
		  writer.writerow(['Country'])
		  for route in self._countries:
			writer.writerow([route])
		c.close()

		with open('wego_cities.csv', 'w') as c:
		  writer = csv.writer(c)
		  writer.writerow(['Country' , 'City'])
		  for route in self._cities:
			city = route[0]
			country = route[1]
			writer.writerow([country , city])
		c.close()

		with open('wego_hotels.csv', 'w') as c:
		  writer = csv.writer(c)
		  writer.writerow(['Country' , 'City' , 'Hotel Name'])
		  for route in self._hotels:
			city = route[1]
			country = route[0]
			hotel = route[2]
			writer.writerow([unicode(country).encode("utf-8") , unicode(city).encode("utf-8") , unicode(hotel).encode("utf-8")])
		c.close()

		with open('wego_hotels_details.csv', 'w') as c:
		  writer = csv.writer(c)
		  writer.writerow(['Country' , 'City' , 'Hotel Name' , 'Hotel Address' , 'Low Price' , 'High Price' , 'Number Of Stars'])
		  for route in self._hotels_details:
			city = route[1]
			country = route[0]
			hotel = route[2]
			address = route[3]
			low_price = route[4]
			high_price = route[5]
			stars = route[6]
			writer.writerow([unicode(country).encode("utf-8") , unicode(city).encode("utf-8") , unicode(hotel).encode("utf-8") , unicode(address).encode("utf-8") , unicode(low_price).encode("utf-8") , unicode(high_price).encode("utf-8") , unicode(stars).encode("utf-8")])
		c.close()


def main():
	parser = WeGoScrapper()
	parser.get_countries()
	parser.save()
	parser.write_to_csv()
	return 1


if __name__ == "__main__":
	sys.exit(main())
