from lxml import etree, html

import csv
import os
import re
import sys

class TravelYaariScrapper(object):

	def __init__(self):
		try:
			f = open('travelyaari_locations.txt')
			self._destinations = eval(f.read())
		except:
			self._destinations = {}
		try:
			f = open('travelyaari_routes.txt')
			self._routes = eval(f.read())
		except:
			self._routes = []

  def save(self):
    print 'Saving'
    output = open('travelyaari_locations.txt', 'w')
    print self._destinations
    output.write(str(self._destinations))
    output.close()
    print self._routes
    output = open('travelyaari_routes.txt', 'w')
    output.write(str(self._routes))
    output.close()

  def _get_tree_from_url(self, url):
    if not url:
      return
    print url
    urlstr = url.replace('/', '_')
    try:
      f = open("dump/%s" % urlstr, 'r')
      doc = html.fromstring(f.read())
      tree = etree.ElementTree(doc)
      print 'Found'
    except:
      print "Error:", sys.exc_info()[0]
      print 'Downloading'
      tree = html.parse(url)
      output = open("dump/%s" % urlstr, 'w')
      output.write(html.tostring(tree))
      output.close()
    return tree

  def _get_duration(self, t):
    duration = 0
    if t.find('NA') == -1:
      t = t.replace(' hrs', '')
      d = t.split(':')
      duration = float(d[0]) + float(d[1])/60
    return duration

  def _parse_row(self, row):
    company = row.find_class('searchpage20')[0].text_content().strip()
    bus_type = row.find_class('searchpage23')[0].text_content().strip()
    dep_time = row.find_class('searchpage24')[0].text_content().strip()
    arr_time = row.find_class('searchpage26')[0].text_content().strip()
    arr_time = arr_time[:8]
    t = row.find_class('searchpage28')[0].text_content().strip()
    duration = self._get_duration(t)
    seats = row.find_class('searchpage31')[0].text_content().strip()
    price_str = row.find_class('searchpage30')[0].text_content().strip().encode("ascii", "ignore")
    price = re.findall("\d+", price_str)
    return (company, bus_type, dep_time, arr_time, duration, seats, price)

  def _parse_route_for_buses(self, url):
    results = []
    tree = self._get_tree_from_url(url)

    rows = tree.findall("//tr[@name='busResults']")
    for row in rows:
      result = self._parse_row(row)
      print result
      results.append(result)
    return results

  def _parse_city_page_for_routes(self, url):
    tree = self._get_tree_from_url(url)

    routes = tree.findall("//div[@class='busroute2']")
    for route in routes:
      link = route.find('a')
      if not link:
        continue
      route_str = link.text_content().strip()
      pair = route_str.split(' to ')
      route_pair = (pair[0].strip(), pair[1].strip())
      #print route_pair
      if route_pair not in self._routes:
        self._routes.append(route_pair)
      route_link = link.get('href')

  def _parse_city_page(self, url):
    tree = self._get_tree_from_url(url)

    tds = tree.findall("//td")
    for td in tds:
      link_tag = td.find('a')
      if link_tag is None:
        continue
      link = link_tag.get('href')
      if not link:
        continue
      #print link
      path = os.path.basename(link)
      parts = path.split('.')[0].split('-')
      #print parts
      dest = parts[-2].title()
      key = int(parts[-1])
      #print dest, key
      if not self._destinations.has_key(dest):
        self._destinations[dest] = key
      self._parse_city_page_for_routes(link)

  def get_destinations(self):
    alpha_range = [''] + ['-%s' % x for x in map(chr, range(65, 91))]
    city_url = "http://www.travelyaari.com/bus-tickets/cities%s.html"
    for char in alpha_range:
      url = city_url % char
      self._parse_city_page(url)
    return self._destinations

  def _clean_dest_from_url(self, token):
    return token.replace("%20", " ").strip().title()

  def _parse_route_page(self, url):
    tree = self._get_tree_from_url(url)

    tds = tree.findall("//td")
    for td in tds:
      link_elem = td.find('a')
      if link_elem is None:
        continue
      link = link_elem.get('href')
      #print link
      path = os.path.basename(link)
      path = path.split('.html')[0].replace("%20", " ")
      keys = re.findall("\d+", path)
      tokens = path.split('-')[:-2]
      dests = ' '.join(tokens).split(' to ')
      #print keys, dests
      # Example parts ['ahmedabad', 'to', 'baroda', '2434', '2455']
      src = self._clean_dest_from_url(dests[0])
      src_key = int(keys[0])
      dest = self._clean_dest_from_url(dests[1])
      dest_key = int(keys[1])
      if not self._destinations.has_key(dest):
        self._destinations[dest] = dest_key
      if not self._destinations.has_key(src):
        self._destinations[src] = src_key
      route_pair = (src.title(), dest.title())
      print route_pair
      if route_pair not in self._routes:
        print 'Adding'
        self._routes.append(route_pair)

  def get_routes(self):
    alpha_range = [''] + ['-%s' % x for x in map(chr, range(65, 91))]
    city_url = "http://www.travelyaari.com/buses-from/routes%s.html"
    for char in alpha_range:
      url = city_url % char
      self._parse_route_page(url)
    return self._routes

  def _parse_operator_page(self, url):
    tree = self._get_tree_from_url(url)

    lis = tree.findall("//li")
    for li in lis:
      link_elem = li.find('a')
      if link_elem is None:
        continue
      link = link_elem.get('href')
      if link.find('buses-from') == -1:
        continue
      #print link
      path = os.path.basename(link)
      path = path.split('.html')[0].replace("%20", " ")
      #print path
      keys = re.findall("\d+", path)
      tokens = path.split('-')[:-2]
      dests = ' '.join(tokens).split(' to ')
      #print keys, dests
      # Example parts ['ahmedabad', 'to', 'baroda', '2434', '2455']
      src = self._clean_dest_from_url(dests[0])
      src_key = int(keys[0])
      dest = self._clean_dest_from_url(dests[1])
      dest_key = int(keys[1])
      if not self._destinations.has_key(dest):
        self._destinations[dest] = dest_key
      if not self._destinations.has_key(src):
        self._destinations[src] = src_key
      route_pair = (src.title(), dest.title())
      print route_pair
      if route_pair not in self._routes:
        print 'Adding'
        self._routes.append(route_pair)

  def _parse_operators_page(self, url):
    tree = self._get_tree_from_url(url)

    tds = tree.findall("//td")
    for td in tds:
      link_elem = td.find('a')
      if link_elem is None:
        continue
      link = link_elem.get('href')
      if not link:
        continue
      self._parse_operator_page(link)

  def get_operators(self):
    alpha_range = [''] + ['-%s' % x for x in map(chr, range(65, 91))]
    operator_url = "http://www.travelyaari.com/travels/operators%s.html"
    for char in alpha_range:
      url = operator_url % char
      self._parse_operators_page(url)

  def ensure_symmetry(self):
    other_routes = []
    for route in self._routes:
      src = route[0]
      dest = route[1]
      reverse_route = (dest, src)
      if reverse_route not in self._routes:
        print str(reverse_route) + " not found"
        other_routes.append(reverse_route)
    self._routes += other_routes

  def write_to_csv(self):
    with open('travelyaari_buses.csv', 'w') as c:
      writer = csv.writer(c)
      writer.writerow(['Route', 'Company', 'Type', 'Departure', 'Arrival', 'Duration', 'Seats', 'Price'])
      for route in self._routes:
        src_key = self._destinations[route[0]]
        dest_key = self._destinations[route[1]]
        url = "http://www.travelyaari.com/search?" \
              "mode=oneway&fromCity=%s|%s&toCity=%s|%s" \
              "&departDate=06-12-2012" % (src_key, route[0], dest_key, route[1])
        route_str = "%s-%s" % route
        buses = self._parse_route_for_buses(url)
        for bus in buses:
          writer.writerow([route_str] + list(bus))
      c.close()

def main():
  parser = TravelYaariScrapper()
  parser.get_destinations()
  parser.get_routes()
  parser.get_operators()
  parser.ensure_symmetry()
  parser.save()
  parser.write_to_csv()
  return 1

if __name__ == "__main__":
   sys.exit(main())
