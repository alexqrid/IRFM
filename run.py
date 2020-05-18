from datetime import datetime
from base64 import b64encode as b64
from elasticsearch.helpers import bulk
from lxml import html
import os
from app import app, es
from app.utils import url, base_url, download, create_index

page = html.fromstring(download(url))
links = page.xpath('//div[@data-versions-items]//a')
links = {i.text[:4]: base_url + i.attrib['href'] for i in links}
title = page.xpath('//span[@class="referenceable"]')[0].text
app.config['links'] = links
app.config['title'] = title

if not os.path.exists(app.config['STATIC_DIR'] + '/reports'):
    """При первом запуке загружаем и индексируем все пдф, поэтому запуск долгий
    проверяем также наличие индекса в эластике"""
    os.mkdir(app.config['STATIC_DIR'] + '/reports')
else:
    if not es.indices.exists(index='reports'):
        if not create_index(es):
            os._exit(1)
        for year, link in links.items():
            if int(year) < 2000:
                break
            path = f'{app.config["STATIC_DIR"]}/reports/report{year}.pdf'
            if os.path.exists(path):
                with open(path, "rb") as fd:
                    document = fd.read()
            else:
                with open(path, 'wb+') as fd:
                    document = download(link)
                    fd.write(download(link))
            es.index(index='reports', doc_type="pdf", id=year, pipeline='attachment',
                         body={
                                 "data": (b64(document)).decode('ascii'),
                             }
                         )


app.run(host="127.0.0.1", port=8080, debug=True)
