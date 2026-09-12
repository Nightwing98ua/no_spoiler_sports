import os

# Ключ API-Football читається зі змінної середовища, а не з коду —
# щоб його ніколи не було видно у файлах проєкту / git-репозиторії.
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY", "")

API_FOOTBALL_BASE_URL = "https://v3.football.api-sports.io"
NHL_BASE_URL = "https://api-web.nhle.com/v1"

# Ті самі ліги, що були у вашому боті
ALLOWED_FOOTBALL_LEAGUES = [1, 39, 140, 135, 78, 61, 2, 3, 848, 137, 81, 45, 333]

# Скільки секунд тримати дані в кеші перед повторним запитом до API
CACHE_TTL_SECONDS = 60 * 60  # 1 година

CACHE_FILE = os.path.join(os.path.dirname(__file__), "cache_store.json")
