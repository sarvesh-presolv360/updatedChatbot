from mangum import Mangum
from api_v2 import app

handler = Mangum(app, lifespan="auto")
