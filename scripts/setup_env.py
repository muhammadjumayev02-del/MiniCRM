"""Create local settings without overwriting an existing .env."""
from pathlib import Path
from secrets import token_urlsafe

env_file = Path(__file__).resolve().parent.parent / '.env'
try:
    with env_file.open('x') as file:
        file.write(
            f'DJANGO_SECRET_KEY={token_urlsafe(48)}\n'
            'DJANGO_DEBUG=True\n'
            'DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1\n'
        )
    env_file.chmod(0o600)
    print('.env yaratildi. Maxfiy kalitni Git ga yubormang.')
except FileExistsError:
    print('.env mavjud; o‘zgartirilmadi.')
