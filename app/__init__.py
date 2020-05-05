from elasticsearch import Elasticsearch
from flask import Flask
from celery import Celery
from app.config import Config
from app.utils import download, url, base_url

app = Flask(__name__)
app.config.from_object(Config)
es = Elasticsearch(app.config['ELASTICSEARCH_URL'],timeout=500)
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

from app import routes

