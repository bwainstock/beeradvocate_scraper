import re
from bs4 import BeautifulSoup
import requests
import argparse
from ba_geo import Bar

def cliargs():

    parser = argparse.ArgumentParser(description='Returns Beer Advocate geodata for City, State')
    parser.add_argument('--state', required=True, help='Two letter state abreviation')
    parser.add_argument('--city', type=str, nargs='+', required=True, help='City')
    args = parser.parse_args()

    return (args.city, args.state)

def getBeer(city, state):

    responses = []
    base_url = 'http://www.beeradvocate.com/place/list/?start=%s&c_id=US&s_id=%s&city=%s&sort=name'

    r = requests.get(base_url % (0, state, '+'.join(city)))
    data = BeautifulSoup(r.content)
    responses.append(data)
    numResults = data.findAll('td', attrs={'bgcolor': '#000000'})
    numResults = numResults[0].text
    numResults = re.findall('(\d+)(?!.*\d)', numResults)
    numResults = int(numResults[0][:-1])

    url_list = [base_url % (start, state, '+'.join(city)) 
                for start in range(20, 20*(numResults/20)+1, 20)]
    for url in url_list:
        r = requests.get(url)
        data = BeautifulSoup(r.content)
        responses.append(data)
    return responses

def parse(response_data):
   
    bars = []
    for data in response_data:
        names = [name.getText() for name in 
                    data.findAll('td', attrs={'colspan': 2, 'align': 'left'})]
        bars.extend(names)
    return bars

if __name__ == '__main__':

    city, state = cliargs()
    r = getBeer(city, state)
    bar_names = parse(r)
    print bar_names, len(bar_names)

