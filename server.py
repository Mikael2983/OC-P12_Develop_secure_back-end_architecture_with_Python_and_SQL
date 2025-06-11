from http.server import HTTPServer

from models.db_model import Base, engine
from models.init_db import init_data_base
from utils import MyHandler

Base.metadata.create_all(bind=engine)
init_data_base()

if __name__ == "__main__":
    port = 8000
    server_address = ("", port)
    httpd = HTTPServer(server_address, MyHandler)
    print(f"Serveur actif sur http://localhost:{port}")
    httpd.serve_forever()
