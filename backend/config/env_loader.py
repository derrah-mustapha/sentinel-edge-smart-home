import os
from dotenv import load_dotenv

def load_environment():
    env = os.getenv("ENV", "local")
    default_env_file = ".env"
    env_specific_file = f".env.{env}"

    print(f"Loading environment profile: {env}")

    if os.path.exists(default_env_file):
        print(f"Using file: {default_env_file}")
        load_dotenv(default_env_file)
        return

    print(f"Using file: {env_specific_file}")
    load_dotenv(env_specific_file)