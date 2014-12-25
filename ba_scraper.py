#!/usr/bin/python3
"""Scrapes beeradvocate.com for geographic information about bars"""

import argparse
import re
from time import sleep

from bs4 import BeautifulSoup
import geopy
from geopy.geocoders import GoogleV3, MapQuest
from geojson import Point, Feature, FeatureCollection
import geojson
import requests

STATES = {
    'AK': 'Alaska',
    'AL': 'Alabama',
    'AR': 'Arkansas',
    'AZ': 'Arizona',
    'CA': 'California',
    'CO': 'Colorado',
    'CT': 'Connecticut',
    'DC': 'District of Columbia',
    'DE': 'Delaware',
    'FL': 'Florida',
    'GA': 'Georgia',
    'HI': 'Hawaii',
    'IA': 'Iowa',
    'ID': 'Idaho',
    'IL': 'Illinois',
    'IN': 'Indiana',
    'KS': 'Kansas',
    'KY': 'Kentucky',
    'LA': 'Louisiana',
    'MA': 'Massachusetts',
    'MD': 'Maryland',
    'ME': 'Maine',
    'MI': 'Michigan',
    'MN': 'Minnesota',
    'MO': 'Missouri',
    'MS': 'Mississippi',
    'MT': 'Montana',
    'NC': 'North Carolina',
    'ND': 'North Dakota',
    'NE': 'Nebraska',
    'NH': 'New Hampshire',
    'NJ': 'New Jersey',
    'NM': 'New Mexico',
    'NV': 'Nevada',
    'NY': 'New York',
    'OH': 'Ohio',
    'OK': 'Oklahoma',
    'OR': 'Oregon',
    'PA': 'Pennsylvania',
    'RI': 'Rhode Island',
    'SC': 'South Carolina',
    'SD': 'South Dakota',
    'TN': 'Tennessee',
    'TX': 'Texas',
    'UT': 'Utah',
    'VA': 'Virginia',
    'VT': 'Vermont',
    'WA': 'Washington',
    'WI': 'Wisconsin',
    'WV': 'West Virginia',
    'WY': 'Wyoming'
}

class Bar(object):
    """Defines a bar with name and geographical information

    geocode(lon, lat): formats a geojson geometry and Feature
    """

    def __init__(self, name, street, city, state, zipcode, categories, rating):
        self.name = name
        self.street = street
        self.city = ' '.join(city)
        self.state = state
        self.zipcode = zipcode
        self.categories = categories
        self.rating = rating
        self.lat = 0
        self.lon = 0
        self.geom = None
        self.feature = None

    def __repr__(self):
        return "Bar: {}".format(self.name)

    def geocode(self, lon, lat):
        """Formats geojson data, including geom and Feature"""
        self.lon = lon
        self.lat = lat
        self.geom = Point((self.lon, self.lat))
        self.feature = Feature(geometry=self.geom,
                               properties={'name': self.name,
                                           'city': self.city,
                                           'state': self.state,
                                           'rating': self.rating,
                                           'categories': self.categories})

def parse(response_data, city, state):
    """Parses names, streets, zipcodes, categories, ratings from responses"""
    for data in response_data:
        names = [name.getText() for name in
                 data.findAll('td', attrs={'colspan': 2, 'align': 'left'})]

        addresses = [address.getText() for address in
                     data.findAll('td', attrs={'class': 'hr_bottom_dark',
                                               'align': 'left'})]
        zipcodes = []
        streets = []
        for address in addresses:
            zipcode_pattern = ''.join(['(?<=', STATES[state], r', )\d{5}'])
            zipcode = re.search(zipcode_pattern, address)
            if zipcode:
                zipcodes.append(zipcode.group())
            else:
                zipcodes.append('')

            street_pattern = ''.join(['.*(?=', ' '.join(city), ')'])
            street = re.search(street_pattern, address)
            if street:
                streets.append(street.group())
            else:
                streets.append('')

        cat_pattern = '\[\\xa0(.*)\\xa0\]'
        raw_categories = [re.findall(cat_pattern, category.getText())[0].split() for category in
                          data.findAll('td', attrs={'class': 'hr_bottom_dark',
                                                    'align': 'right'})]
        categories = [[cat.strip(',') for cat in cat_list]
                      for cat_list in raw_categories]

        ratings = [float(rating.getText()) if rating.getText() != '-' else 'null'  for rating in
                   data.findAll('td', attrs={'class': 'hr_bottom_light'})[::4]]

        return [Bar(name, street, city, state, zipcode, cats, rating)
                for name, street, zipcode, cats, rating in
                zip(names, streets, zipcodes, categories, ratings)]

def geocoder(bars):
    """Geocodes bar information using GoogleV3 API and returns geoJSON FeatureCollection"""
    #geolocator = GoogleV3()
    geolocator = MapQuest('Fmjtd%7Cluurn901nh%2Caw%3Do5-9wt51w', timeout=3)
    for bar in bars:
        if bar.zipcode:
            print(bar.name)
            try:
                location = geolocator.geocode(' '.join([bar.street, bar.zipcode]))
            except geopy.exc.GeocoderUnavailable as error:
                print(error)
            else:
                bar.geocode(location.longitude, location.latitude)
            sleep(.2)

    return [bar.feature for bar in bars if bar.zipcode]

def get_cities(state):
    """Parses two columns of cities for given STATES from BeerAdvocate url"""
    url = 'http://www.beeradvocate.com/place/directory/9/US/{}/'.format(state)
    response = requests.get(url)
    data = BeautifulSoup(response.content)

    tables = data.findAll('table',
                          attrs={'width': '100%',
                                 'border': '0',
                                 'cellspacing': '0',
                                 'cellpadding': '2'})
    for table in tables:
        if 'Cities & Towns' in table.findChild().text:
            cities = [city.text.split() for city in table.findAll('li')]

    return cities

def get_beer(city, state):
    """Determines maximum # of ratings and returns list of response data."""
    responses = []
    base_url = 'http://www.beeradvocate.com/place/list/?start={}&c_id=US&s_id={}&city={}&sort=name'
    response = requests.get(base_url.format(0, state, '+'.join(city)))
    if 'fail' not in response.url: # If no entries exist for given city, url will include fail
        data = BeautifulSoup(response.content)
        responses.append(data)
        num_results = data.findAll('td', attrs={'bgcolor': '#000000'})
        num_results = num_results[0].text
        num_results = re.findall(r'(\d+)(?!.*\d)', num_results)
        num_results = int(num_results[0])

        url_list = [base_url.format(start, state, '+'.join(city))
                    for start in range(20, 20 * (num_results // 20) + 1, 20)]
        for url in url_list:
            response = requests.get(url)
            data = BeautifulSoup(response.content)
            responses.append(data)

    return responses

def ba_to_json(cities, states):
    """Creates directory structure and writes geojson data to file '/state/city_state.json'"""
    print(states, cities)
    features = []
    
    for state in states:
        if cities is None:
            cities = get_cities(state)
        for city in cities:
            print('\n'.join(["*"*10, ' '.join(city), "*"*10, state, "*"*10]))
            response = get_beer(city, state)
            if response:
                bars = parse(response, city, state)
                features.extend(geocoder(bars))

    if len(cities) is 1:
        city = cities[0]
        city_name = '_'.join(city)
        city_state = '_'.join([city_name, state])
        output_file = '.'.join([city_state, 'json']).lower()
    elif len(states) is 1:
        print(len(states))
        output_file = '.'.join([states[0], 'json']).lower()
    else:
        output_file = 'usa.json'

    features_to_json(features, output_file)
    return output_file

def json_to_cartodb(cartodb, output_file):
    """Utilizes the CartoDB Import API to upload json file"""
    url = 'https://{}.cartodb.com/api/v1/imports/?api_key={}'.format(cartodb[0], cartodb[1])
    response = requests.post(url, files={'file': open(output_file, 'rb')})
    if response.json()['success']:
        table_id = response.json()['item_queue_id']
        print('File successfully uploaded to CartoDB')
        url = 'https://{}.cartodb.com/api/v1/imports/{}?api_key={}'.format(cartodb[0],
                                                                           table_id,
                                                                           cartodb[1])
        response = requests.get(url)
        table_name = response.json()['table_name']
        print('https://{}.cartodb.com/tables/{}'.format(cartodb[0], table_name))
    else:
        print('There was an error with your upload.')

def features_to_json(features, filename):
    """Accepts a list of Features and outputs a FeatureCollection json file"""
    featurecollection = FeatureCollection(features)
    
    if not filename.endswith('.json'):
        filename = ''.join([filename, '.json'])

    with open(filename, 'a') as geofile:
        geojson.dump(featurecollection, geofile)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Returns Beer Advocate geodata for City, State')
    parser.add_argument(
        '--city', type=str, nargs='+', help='City')
    parser.add_argument(
        '--state', help='Two letter state abreviation')
    parser.add_argument('--usa', action='store_true', help='Parses all of USA locations')
    parser.add_argument(
        '--cartodb', type=str, nargs=2, help='Upload resulting file to CartoDB Format: user key')
    args = parser.parse_args()

    
    if args.usa: #All of USA
        CITY = None
        #STATE = iter(STATES.keys())
        STATE = STATES.keys()
    elif args.city: #Just one city
        CITY = [args.city]
        STATE = [args.state]
    else: #All of state
        CITY = None 
        STATE = [args.state]

    OUTPUT_FILE = ba_to_json(CITY, STATE)

    if args.cartodb:
        ba_to_cartodb(args.cartodb, OUTPUT_FILE)
