import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?"
        f"ssl_ca={os.path.join(os.getcwd(), 'ca-cert.pem')}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable track modifications for performance
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
