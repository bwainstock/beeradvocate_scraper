import re
from bs4 import BeautifulSoup
import requests
import argparse
import geojson
from time import sleep
from geopy.geocoders import GoogleV3
from geojson import Point, Feature, FeatureCollection


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


def cliargs():
    """Returns --city and --state as arguments for BeerAdvocate parser"""
    parser = argparse.ArgumentParser(
        description='Returns Beer Advocate geodata for City, State')
    parser.add_argument(
        '--city', type=str, nargs='+', required=True, help='City')
    parser.add_argument(
        '--state', required=True, help='Two letter state abreviation')
    args = parser.parse_args()

    return (args.city, args.state)


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


def parse(response_data):
    """Parses names, streets, zipcodes, categories, ratings from responses"""

    bars = []
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

        ratings = [rating.getText() for rating in
                   data.findAll('td', attrs={'class': 'hr_bottom_light'})[::4]]
        bars.extend([{'name': name,
                      'street': street,
                      'zipcode': zipcode,
                      'categories': cats,
                      'rating': rating}
                    for name, street, zipcode, cats, rating in
                        zip(names, streets, zipcodes, categories, ratings)])
    return bars

def geocoder(bars):
    """Geocodes bar information using GoogleV3 API and returns geoJSON FeatureCollection"""
    geolocator = GoogleV3()

    for index, bar in enumerate(bars):
        
        if bar['zipcode']:
            location = geolocator.geocode(' '.join([bar['street'], bar['zipcode']]))
            bars[index]['index'] = index
            bars[index]['lat'] = location.latitude
            bars[index]['lon'] = location.longitude
            bars[index]['geom'] = Point((location.longitude, location.latitude))
            sleep(.2)

    return FeatureCollection([Feature(geometry=bar['geom'], id=bar['index'],
                             properties={'name': bar['name'],
                                         'rating': bar['rating'],
                                         'categories': bar['categories']})
                             for bar in bars if bar['zipcode']])

if __name__ == '__main__':

    CITY, STATE = cliargs()
    RESPONSE = get_beer(CITY, STATE)
    BARS = parse(RESPONSE)
    with open(''.join([''.join(CITY), '.json']).lower(), 'w') as FILE:
        geojson.dump(geocoder(BARS), FILE)
