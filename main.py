import io

from fastapi.openapi.models import Response
from starlette.responses import FileResponse, StreamingResponse

from modules.client import StellaAPI

app = StellaAPI()


def create_image_response(_bytes):
    return Response(content=_bytes, media_type="image/png")

@app.get('/github/banner', responses = {
        200: {
            "content": {"image/png": {}}
        }
    }, response_class=StreamingResponse)
async def get_generated_banner():
    banner = await app.generate_banner()
    image_stream = io.BytesIO(banner)
    return StreamingResponse(content=image_stream, media_type="image/png")


@app.get('/github/default')
async def get_default_banner():
    return FileResponse('assets/default-banner.png')


@app.on_event('startup')
async def on_startup():
    await app.startup()

@app.on_event('shutdown')
async def on_shutdown():
    await app.cleanup()

