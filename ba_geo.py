import re
import json
from geopy.geocoders import Nominatim

geolocator = Nominatim()

class Bar(object):
    def __init__(self, name, rating=0, address='', lon=0, lat=0,
                 geom=''):
        self.name = name
        self.rating = rating

        self.address, self.lon, self.lat, self.geom = self._geocode(address)

    def __repr__(self):
        return 'Bar: %s' % self.name

    def _geocode(self, address):
        
        def trunc_address(address):
            r = re.compile('[0-9][U]')
            match = r.findall(address)

            addr_end = address.index(match[0]) + 1
            return address[:addr_end]

        def split_address(address):
            lower_upper = re.compile('[a-z][A-Z]').findall(address)
            formatted_addr = address
           
            if lower_upper:
                split_spot = address.index(lower_upper[0]) + 1
                formatted_addr = (address[:split_spot] + ' ' + address[split_spot:])

            upper_upper = re.compile('[A-Z][A-Z]').findall(formatted_addr)

            if upper_upper:
                split_spot = formatted_addr.index(upper_upper[0]) + 1
                formatted_addr = (formatted_addr[:split_spot] + ' ' + formatted_addr[split_spot:])

            try:
                dash = formatted_addr.index('-') 
            except:
                dash = ''

            if dash:
                return formatted_addr[:dash]
            else:
                return formatted_addr

        truncated_address = trunc_address(address)
        split_address = split_address(truncated_address)
        
        try:
            location = geolocator.geocode(split_address, timeout=5)
        except:
            location = ''

        print truncated_address
        print split_address
        if location:
            print location.address
            return (split_address, location.longitude, location.latitude, 
                location.point)
        else:
            return ('None', 'None', 'None', 'None')

#with open('ba_sc.json', 'r') as f:
#    data = json.load(f)

#raw_bars = data[u'results'][u'collection1']
#bars = []

#for bar in raw_bars:
#    bars.append(Bar(name=bar[u'Name'].encode('utf-8'),
#                    rating=bar[u'Rating'].encode('utf-8'),
#                   address=bar[u'Address']))

