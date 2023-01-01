import io

from starlette.responses import FileResponse, StreamingResponse

from modules.client import StellaAPI

app = StellaAPI()


@app.get('/github/banner', response_class=StreamingResponse)
async def get_generated_banner() -> StreamingResponse:
    banner = await app.generate_banner()
    image_stream = io.BytesIO(banner)
    return StreamingResponse(content=image_stream, media_type="image/png")


@app.get('/github/default', response_class=FileResponse)
async def get_default_banner() -> FileResponse:
    return FileResponse('assets/default-banner.png')


@app.on_event('startup')
async def on_startup() -> None:
    await app.startup()


@app.on_event('shutdown')
async def on_shutdown() -> None:
    await app.cleanup()

