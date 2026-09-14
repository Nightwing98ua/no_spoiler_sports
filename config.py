import os

NHL_BASE_URL = "https://api-web.nhle.com/v1"

# Скільки секунд тримати дані в кеші перед повторним запитом до API
CACHE_TTL_SECONDS = 60 * 60  # 1 година

CACHE_FILE = os.path.join(os.path.dirname(__file__), "cache_store.json")
