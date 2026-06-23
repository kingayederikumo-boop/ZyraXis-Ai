from app.config import Config


def bootstrap():
    # Fail-fast validation of environment before any service starts
    Config.validate()


if __name__ == "__main__":
    bootstrap()
    print("ZyraXis bootstrap validation passed.")
