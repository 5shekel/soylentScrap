import json
import requests
import re
import numpy as np

import config

from bs4 import BeautifulSoup as bs

def text_match(text, pattern):
    if text == pattern:
        return True
    else:
        return False

def get_list_urls_military_nuts(url):
    r = requests.get(url)
    raw_content = r.content
    soup = bs(raw_content, 'html.parser')
    pagination = soup.findAll('table')[4]
    pages = pagination.select('a')
    text_pages = map(lambda x: x.text, pages)
    last_page = np.array(map(lambda x: text_match(x, u'Last \xbb'), text_pages))
    last_index = np.where(last_page)[0][0]

    last_page_url = pages[last_index].get('href')
    last_number = int(re.findall('(?<=\&st\=)[0-9]+', last_page_url)[0])
    url_string = re.findall('^(.*?)[0-9]+$', last_page_url)[0]
    page_numbers = range(0, last_number + 20, 20)

    url_to_scrape = [url_string + str(x) for x in page_numbers]
    return url_to_scrape


def get_username(content):
    try:
        name = content.find('span', {'class' : 'normalname'}).text
        return name
    except:
        return None

def get_date(content):
    try:
        date_pattern = re.compile("(Posted:)\W", re.I)
        post_details = content.find('span', {'class' : 'postdetails'}).text
        date = date_pattern.sub("", post_details)
        return date
    except:
        return None

def get_post(content):
    try:
        post_entry = content.findAll('td', {'valign' : 'top'})[2]
        posts = post_entry.findAll('div', {'class' : 'postcolor'})
        post_text = ''
        for post in posts:
            post_text += post.text.strip()
        post_text = post_text.strip()
        if post_text != '':
            return post_text
        else:
            return None
    except:
        return None

def get_contents(content):
    name = get_username(content)
    date = get_date(content)
    post = get_post(content)
    if name and date and post:
        data = {'name' : name, 'date' : date, 'text' : post}
        return data
    else:
        return False


if __name__ == '__main__':
    url_to_scrape = get_list_urls_military_nuts('http://militarynuts.com/index.php?showtopic=1577')
    data = []

    for url in url_to_scrape:
        r = requests.get(url)
        raw_content = r.content
        soup = bs(raw_content, 'lxml')
        #soup = bs(raw_content, 'html.parser')

        all_tables = soup.find_all('table', {'cellpadding' : '3'}, recursive=True)
        for content in all_tables:
            information = get_contents(content)
            if information:
                data.append(information)

    #with open(config.MN_DATA, mode = 'w') as f:
    with open("output.txt", mode = 'w') as f:
        json.dump(data, f)
