# Define the application directory
import os

# Statement for enabling the development environment
class Config(object):
    DEBUG = True

    CELERY_BROKER_URL = "redis://:f858bf5a779be228d9003d6d44725c6824d38f9a56c86cb4e0db33f801470b98@127.0.0.1:6000/0"
    CELERY_RESULT_BACKEND = "redis://:f858bf5a779be228d9003d6d44725c6824d38f9a56c86cb4e0db33f801470b98@127.0.0.1:6000/0"

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    STATIC_DIR = os.path.abspath(BASE_DIR + "/static")
    # Define the database - we are working with
    # SQLite for this example
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'app.db')
    DATABASE_CONNECT_OPTIONS = {}

    # Application threads. A common general assumption is
    # using 2 per available processor cores - to handle
    # incoming requests using one and performing background
    # operations using the other.
    THREADS_PER_PAGE = 2

    # Enable protection agains *Cross-site Request Forgery (CSRF)*
    CSRF_ENABLED = False

    # Use a secure, unique and absolutely secret key for
    # signing the data.
    CSRF_SESSION_KEY = "secret"

    # Secret key for signing cookies
    SECRET_KEY = "secret"
