import requests as r

base_url = "https://cbr.ru"
url = "https://cbr.ru/about_br/publ/god/"


def download(url):
    source = r.get(url)
    return source.content


def create_index(es):
    pipeline = {
        "description": "Extract attachment information. Used to parse pdf and office files",
        "processors": [
            {
                "attachment": {
                    "field": "data",
                    "indexed_chars": -1
                }
            }
        ]
    }
    response = es.ingest.put_pipeline(id='attachment', body=pipeline)
    if response['acknowledged']:
        body = {"settings": {
                    "highlight.max_analyzed_offset": 1000000000,
                    "analysis": {
                      "filter": {
                          "ru_stop": {
                          "type": "stop",
                          "stopwords": "_russian_"
                        },
                        "ru_stemmer": {
                          "type": "stemmer",
                          "language": "russian"
                        }
                      },
                      "analyzer": {
                        "rus": {
                          "char_filter": [
                            "html_strip"
                          ],
                          "tokenizer": "standard",
                          "filter": [
                            "lowercase",
                            "ru_stop",
                            "ru_stemmer",
                          ]
                        }
                      }
                    }
                  }
             }
        response = es.indices.create(index='reports', body=body)
    return response['acknowledged']