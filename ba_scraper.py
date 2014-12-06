import argparse
import re
from time import sleep

from bs4 import BeautifulSoup
from geopy.geocoders import GoogleV3
from geojson import Point, Feature, FeatureCollection
import geojson
import requests

STATES = {
    'AK': 'Alaska',
    'AL': 'Alabama',
    'AR': 'Arkansas',
    'AS': 'American Samoa',
    'AZ': 'Arizona',
    'CA': 'California',
    'CO': 'Colorado',
    'CT': 'Connecticut',
    'DC': 'District of Columbia',
    'DE': 'Delaware',
    'FL': 'Florida',
    'GA': 'Georgia',
    'GU': 'Guam',
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
    'MP': 'Northern Mariana Islands',
    'MS': 'Mississippi',
    'MT': 'Montana',
    'NA': 'National',
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
    'PR': 'Puerto Rico',
    'RI': 'Rhode Island',
    'SC': 'South Carolina',
    'SD': 'South Dakota',
    'TN': 'Tennessee',
    'TX': 'Texas',
    'UT': 'Utah',
    'VA': 'Virginia',
    'VI': 'Virgin Islands',
    'VT': 'Vermont',
    'WA': 'Washington',
    'WI': 'Wisconsin',
    'WV': 'West Virginia',
    'WY': 'Wyoming'
}

class Bar(object):
    def __init__(self, name, street, zipcode, categories, rating):
        self.name = name
        self.street = street
        self.zipcode = zipcode
        self.categories = categories
        self.rating = rating
        self.lat = 0
        self.lon = 0
        self.geom = None
        self.feature = None
    def __repr__(self):
      return "Bar: %s" % self.name
    def geocode(self, lon, lat):
        self.lat = lat
        self.lon = lon
        self.geom = Point((self.lon, self.lat))
        self.feature = Feature(geometry=self.geom,
                               properties={'name': self.name,
                                           'rating': self.rating,
                                           'categories': self.categories})
    

def cliargs():
    """Returns --city and --state as arguments for BeerAdvocate parser"""
    parser = argparse.ArgumentParser(
        description='Returns Beer Advocate geodata for City, State')
    parser.add_argument(
        '--city', type=str, nargs='+', help='City')
    parser.add_argument(
        '--state', required=True, help='Two letter state abreviation')
    args = parser.parse_args()
    
    city = args.city
    state = args.state

    if city:
        return city, state

    return (get_cities(state), state)


def get_beer(city, state):
    """Determines maximum # of ratings and returns list of response data"""
    responses = []
    base_url = 'http://www.beeradvocate.com/place/list/?start=%s&c_id=US&s_id=%s&city=%s&sort=name'

    response = requests.get(base_url % (0, state, '+'.join(city)))
    data = BeautifulSoup(response.content)
    responses.append(data)
    num_results = data.findAll('td', attrs={'bgcolor': '#000000'})
    num_results = num_results[0].text
    num_results = re.findall(r'(\d+)(?!.*\d)', num_results)
    num_results = int(num_results[0])

    url_list = [base_url % (start, state, '+'.join(city))
                for start in range(20, 20 * (num_results // 20) + 1, 20)]
    for url in url_list:
        response = requests.get(url)
        data = BeautifulSoup(response.content)
        responses.append(data)
    return responses

def get_cities(state):
    """Parses cities of given STATES from BeerAdvocate url"""
    cities = []
    url = 'http://www.beeradvocate.com/place/directory/9/US/AL/'
    r = requests.get(url)
    data = BeautifulSoup(data)

    raw_cities = data.findAll('td',
                              attrs={'align': 'left', 'valign': 'top', 'width': '50%'})
    cities = {'AL', [city.text for city in raw_cities[2].findAll('li')]}

def parse(response_data):
    """Parses names, streets, zipcodes, categories, ratings from responses"""
    # bars = []
    for data in response_data:
        names = [name.getText() for name in
                 data.findAll('td', attrs={'colspan': 2, 'align': 'left'})]

        addresses = [address.getText() for address in
                     data.findAll('td', attrs={'class': 'hr_bottom_dark',
                                               'align': 'left'})]
        zipcodes = []
        streets = []
        for address in addresses:
            zipcode_pattern = ''.join(['(?<=', STATES[STATE], r', )\d{5}'])
            zipcode = re.search(zipcode_pattern, address)
            if zipcode:
                zipcodes.append(zipcode.group())
            else:
                zipcodes.append('')

            street_pattern = ''.join(['.*(?=', ' '.join(CITY), ')'])
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
                   
        return [Bar(name, street, zipcode, cats, rating)
                for name, street, zipcode, cats, rating in
                zip(names, streets, zipcodes, categories, ratings)]
        
        # bars.extend([{'name': name,
        #               'street': street,
        #               'zipcode': zipcode,
        #               'categories': cats,
        #               'rating': rating}
        #             for name, street, zipcode, cats, rating in
        #                 zip(names, streets, zipcodes, categories, ratings)])
    # return bars

def geocoder(bars):
    """Geocodes bar information using GoogleV3 API and returns geoJSON FeatureCollection"""
    geolocator = GoogleV3()

    for bar in bars:
        
        if bar.zipcode:
            location = geolocator.geocode(' '.join([bar.street, bar.zipcode]))
            # bars[index]['index'] = index
            # bars[index]['lat'] = location.latitude
            # bars[index]['lon'] = location.longitude
            # bars[index]['geom'] = Point((location.longitude, location.latitude)
            bar.geocode(location.longitude, location.latitude)
            sleep(.2)

    return FeatureCollection([bar.feature for bar in bars if bar.zipcode])

#def toCartoDB(GEOJSON):
#    """Uploads file to CartoDB"""
#
#    r = requests.post(url, files={'file': open('FILENAME', 'rb')})
#
def write_geojson(geojson_data):
    """Creates directory structure and writes geojson data to file '/state/city_state.json'"""

    
if __name__ == '__main__':

    CITY, STATE = cliargs()
    RESPONSE = get_beer(CITY, STATE)
    JSON = parse(RESPONSE)
    with open(''.join([''.join(CITY), '_', STATE, '.json']).lower(), 'w') as FILE:
        geojson.dump(geocoder(JSON), FILE)
