# gunicorn -b "127.0.0.1:8080" hproxy:app

import requests
from bs4 import BeautifulSoup
from bs4.element import Comment
import re


def tag_visible(e):
    vis = ['style', 'script', 'head', 'title', 'meta', '[document]']
    if e.parent.name in vis:
        return False
    if isinstance(e, Comment):
        return False
    return True


def add_tm(msg):
    words = re.split('(\W)', msg)
    return "".join([x + '™' if len(x) == 6 else x for x in words])


def app(env, start_response):
    uri = env['RAW_URI']
    agent = env['HTTP_USER_AGENT']

    url = 'http://habrahabr.ru' + uri
    headers = {'user-agent': agent}

    page = requests.get(url, headers=headers)

    if uri.endswith(('.woff', '.woff2', '.ttf', '.css', '.js')):
        return iter(page)

    soup = BeautifulSoup(page.content, 'html.parser')

    for a in soup.findAll('a'):
        addr = 'http://127.0.0.1:' + env['SERVER_PORT']
        a['href'] = a.get('href', '').replace("https://habrahabr.ru", addr)

    tags = soup.findAll(text=True)
    visible_tags = filter(tag_visible, tags)

    for t in visible_tags:
        old = t.string
        new = old.replace('&plus;', '+')
        t.string.replace_with(add_tm(new))

    data = str(soup)

    start_response("200 OK", [
        ("Connection", "keep-alive"),
        ("Content-Type", "text/html; charset=UTF-8"),
    ])

    return iter([data.encode()])
