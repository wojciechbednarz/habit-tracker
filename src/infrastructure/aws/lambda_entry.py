from mangum import Mangum

from src.api.main import app

lambda_handler = Mangum(app=app, lifespan="off")
