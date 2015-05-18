from bs4 import BeautifulSoup
import requests
import csv
from array import *

searcharray = []
r  = requests.get("http://www.medicinenet.com/procedures_and_tests/alpha_z.htm")
data = r.text
soup = BeautifulSoup(data)

for link1 in soup.find_all('div' , class_="AZ_results"):
	for link2 in link1.find_all('ul'):
		for link3 in link2.find_all('a'):
			print(link3.text)
			searcharray.append(link3.text)
print (searcharray)

csv_out = open("tests.csv" , "a")
my_writer = csv.writer(csv_out, lineterminator='\n')
for row in zip(searcharray):
	my_writer.writerow(row)
csv_out.close()
