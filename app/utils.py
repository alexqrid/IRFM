import requests as r

base_url = "https://cbr.ru"
url = "https://cbr.ru/about_br/publ/god/"


def download(url):
    source = r.get(url)
    return source.content



