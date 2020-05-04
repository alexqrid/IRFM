from datetime import datetime
from base64 import b64encode as b64
from elasticsearch.helpers import bulk
from lxml import html
import os
from app import app, es
from app.utils import url, base_url, download

page = html.fromstring(download(url))
links = page.xpath('//div[@data-versions-items]//a')
links = {i.text[:4]: base_url + i.attrib['href'] for i in links}
title = page.xpath('//span[@class="referenceable"]')[0].text
app.config['links'] = links
app.config['title'] = title

if not os.path.exists(app.config['STATIC_DIR'] + '/reports'):
    """При первом запуке загружаем и индексируем все пдф"""
    os.mkdir(app.config['STATIC_DIR'] + '/reports')
    docs = []
    for year, link in links.items():
        with open(f'{app.config["STATIC_DIR"]}/reports/report{year}.pdf', 'wb+') as fd:
            document = download(link)
            fd.write(download(link))
        docs.append({"_index": "reports",
                "_type": "pdf",
                "pipeline": "attachment",
                "source": (b64(document)).decode('ascii'),
                "added_date": datetime.now().strftime('%d.%m.%Y %H:%M:%S')
                })
    bulk(es, docs)

app.run(host="127.0.0.1", port=8080, debug=True)
