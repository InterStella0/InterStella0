from fastapi import FastAPI

from modules.images import ImageHandler


class StellaAPI(FastAPI):
    def __init__(self) -> None:
        super().__init__()
        self.image_handler = ImageHandler()

    async def startup(self) -> None:
        await self.image_handler.acquire_github()

    async def generate_banner(self) -> bytes:
        return await self.image_handler.generate_banner()

    async def cleanup(self) -> None:
        await self.image_handler.cleanup()
