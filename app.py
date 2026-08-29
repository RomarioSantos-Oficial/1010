import socket

import uvicorn

from config.settings import settings


def port_is_in_use(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


if __name__ == "__main__":
    if port_is_in_use(settings.host, settings.port):
        print(
            f"A porta {settings.port} já está em uso. "
            f"Se a Luna já estiver aberta, acesse http://{settings.host}:{settings.port}. "
            "Não inicie uma segunda instância com o mesmo armazenamento local."
        )
        raise SystemExit(0)
    uvicorn.run("api.server:app", host=settings.host, port=settings.port, reload=False)
