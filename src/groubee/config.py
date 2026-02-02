from dotenv import load_dotenv, find_dotenv

load_dotenv(verbose=True, override=True, dotenv_path=find_dotenv())

LISTENER_HOST = "localhost"
LISTENER_PORT = 5001
