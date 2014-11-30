import re
from bs4 import BeautifulSoup
import requests
import argparse


def cliargs():

    parser = argparse.ArgumentParser(
        description='Returns Beer Advocate geodata for City, State')
    parser.add_argument(
        '--state', required=True, help='Two letter state abreviation')
    parser.add_argument(
        '--city', type=str, nargs='+', required=True, help='City')
    args = parser.parse_args()

    return (args.city, args.state)


def get_beer(city, state):

    responses = []
    base_url = 'http://www.beeradvocate.com/place/list/?start=%s&c_id=US&s_id=%s&city=%s&sort=name'

    response = requests.get(base_url % (0, state, '+'.join(city)))
    data = BeautifulSoup(response.content)
    responses.append(data)
    num_results = data.findAll('td', attrs={'bgcolor': '#000000'})
    num_results = num_results[0].text
    num_results = re.findall('(\d+)(?!.*\d)', num_results)
    num_results = int(num_results[0])

    url_list = [base_url % (start, state, '+'.join(city))
                for start in range(20, 20 * (num_results // 20) + 1, 20)]
    for url in url_list:
        response = requests.get(url)
        data = BeautifulSoup(response.content)
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
    response = get_beer(city, state)
    bar_names = parse(response)
    print(len(bar_names))
