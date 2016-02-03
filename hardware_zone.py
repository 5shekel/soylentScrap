import json
import requests
import re
import numpy as np
import os.path
import config

from bs4 import BeautifulSoup as bs

def text_match(text, pattern):
    if text == pattern:
        return True
    else:
        return False

def get_url(url):
    r = requests.get(url)
    if r.status_code == 200:
        return r.content
    else:
        print('Error: {}'.format(r.status_code))
        return None

def clean_text(text):
    ctext = text.replace('\r', ' ').replace('\t', ' ').replace('\r', ' ')
    return ctext

def hz_next_url(base, url):
    try:
        url_string = base + url
        raw_content = get_url(url_string)
        soup = bs(raw_content, 'lxml')
        container = soup.body.find('div', {'id' : 'container'})
        forum_table = container.find('table', {'id' : 'forum-ads-table'})
        pagination_section = container.find('div', {'class' : 'pagination'})
        nav_sections = pagination_section.findAll('li', {'class' : 'prevnext'})
        nav_text = map(lambda x: x.text, nav_sections)
        next_boolean = np.array(map(lambda x: text_match(x, u'Next \u203a'), nav_text))
        next_index = np.where(next_boolean)[0][0]
        next_url = nav_sections[next_index].find('a').get('href')
        return next_url
    except:
        return None

def get_forum_urls(base, url, list_array = []):
    url_string = base + url
    list_array.append(url_string)
    next_url = hz_next_url(base, url)
    if next_url:
        return get_forum_urls(base, next_url, list_array)
    else:
        return list_array

def get_thread_urls(base_url, forum_url):
    raw_content = get_url(forum_url)
    soup = bs(raw_content, 'lxml')
    container = soup.body.find('div', {'id' : 'container'})
    forum_table = container.find('table', {'id' : 'forum-ads-table'})
    threads_table = forum_table.find('table', {'class' : 'tborder', 'id' : 'threadslist'})
    threads_tbody = threads_table.findAll('tbody')
    main_threads_tbody = threads_tbody[1]
    threads_rows = main_threads_tbody.findAll('tr', { 'class' : None })
    thread_urls = []
    for row in threads_rows:
        thread_url = row.find('td', title=True, class_='alt1').find('a').get('href')
        thread_urls.append(base_url + thread_url)
    return thread_urls

def get_username(content):
    try:
        name = content.find('a', {'class' : 'bigusername'}).text.strip()
        return name
    except:
        return None

def get_date(content):
    try:
        date = content.find('td', {'class' : 'thead'}).text.strip()
        return date
    except:
        return None

def get_text(content):
    try:
        container = content.find('td', {'class' : 'alt1'})
        text = ''
        post_texts = container.find('div', id=True).findAll(text=True, recursive=False)
        for post_text in post_texts:
            text += ' ' + clean_text(post_text).strip()
        return text.strip()
    except:
        return None

def get_contents(content):
    try:
        name = get_username(content)
        date = get_date(content)
        text = get_text(content)
        if name and date and text:
            post = {'name' : name, 'date' : date, 'text' : text}
            return post
        else:
            return None
    except:
        return None

def get_hz_page(url):
    raw_content = get_url(url)
    soup = bs(raw_content, 'lxml')
    container = soup.body.find('div', {'id' : 'container'})
    forum_table = container.find('table', {'id' : 'forum-ads-table'})
    div_posts = forum_table.find('div', {'id' : 'posts'})
    div_post_wrapper = div_posts.findAll('div', {'class' : 'post-wrapper'})
    posts = []
    for post_wrapper in div_post_wrapper:
        content = post_wrapper.find('table', {'class' : 'post'})
        post = get_contents(content)
        if post:
            posts.append(post)
    return posts

def next_hz_page(base, url):
    try:
        raw_content = get_url(url)
        soup = bs(raw_content, 'lxml')
        container = soup.body.find('div', {'id' : 'container'})
        forum_table = container.find('table', {'id' : 'forum-ads-table'})
        pagination_section = container.find('div', {'class' : 'pagination'})
        nav_sections = pagination_section.findAll('li', {'class' : 'prevnext'})
        nav_text = map(lambda x: x.text, nav_sections)
        next_boolean = np.array(map(lambda x: text_match(x, u'Next \u203a'), nav_text))
        next_index = np.where(next_boolean)[0][0]
        next_url = nav_sections[next_index].find('a').get('href')
        return base + next_url
    except:
        return None

def get_hz_thread(base, url):
    try:
        thread = []
        current_url = url
        while True:
            posts = get_hz_page(current_url)
            thread += posts
            next_url = next_hz_page(base, current_url)
            if next_url:
                current_url = next_url
            else:
                return thread
    except:
        return None

def add_json(filename, json_data):
    if os.path.isfile(filename):
        fexists = True
    else:
        fexists = False
    if fexists:
        with open(filename, mode='r') as f:
            feeds = json.load(f)
    else:
        feeds = []
    with open(filename, mode='w') as f:
        feeds.extend(json_data)
        json.dump(feeds, f)

def add_scraped(filename, new_line):
    if os.path.isfile(filename):
        fexists = True
    else:
        fexists = False
    if fexists:
        with open(filename, mode='r') as f:
            lines = [line for line in f if line.strip()]
    with open(filename, mode='w') as f:
        if fexists:
            for line in lines:
                f.write(line + '\n')
        f.write(new_line + '\n')

def get_scraped(filename):
    if os.path.isfile(filename):
        with open(filename, mode='r') as f:
            lines = [line for line in f if line.strip()]
        return lines
    else:
        return []

if __name__ == '__main__':
    file_scraped = "out2" #config.HZ_SCRAPED
    hz_json_data = "out1" #config.HZ_DATA
    base_url = 'http://forums.hardwarezone.com.sg'
    forum_urls = get_forum_urls(base_url, '/national-service-knowledge-base-162/')
    thread_urls = []
    for forum_url in forum_urls:
        urls = get_thread_urls(base_url, forum_url)
        thread_urls.extend(urls)

    scraped = get_scraped(file_scraped)
    for thread_url in thread_urls:
        if thread_url not in scraped:
            print('Scraping: {}'.format(thread_url))
            thread = get_hz_thread(base_url, thread_url)
            add_scraped(file_scraped, thread_url)
            add_json(hz_json_data, thread)
