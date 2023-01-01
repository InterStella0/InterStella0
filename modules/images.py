from __future__ import annotations
import asyncio
import dataclasses
import datetime
import io
import os
import textwrap
from typing import Optional

import PIL
import humanize
from PIL.Image import Image
from PIL.ImageDraw import ImageDraw
from PIL import ImageFont
from PIL.ImageFont import FreeTypeFont

from modules.github import StellaGithub, RepoCommit


@dataclasses.dataclass
class Position:
    x: int
    y: int
    width: int
    height: int


class CommitAwareImage:
    font_name: str = 'ARLRDBD.TTF'
    padding: int = 5

    def __init__(self, repo_commit: RepoCommit) -> None:
        self.filename: str = 'commit-aware.png'
        self.font: Optional[FreeTypeFont] = None
        self.font_dir: str = ""
        self.commit_repo: RepoCommit = repo_commit
        self._bytes: Optional[bytes] = None
        self._image: Optional[Image] = None
        self._draw: Optional[ImageDraw] = None

    def create_font(self, size: int) -> ImageFont:
        return ImageFont.truetype(self.font_dir, size)

    @classmethod
    def load(cls, directory: str, repo_commit: RepoCommit) -> CommitAwareImage:
        self = cls(repo_commit)
        self.font_dir = os.path.join(directory, self.font_name)
        self.font = self.create_font(13)
        return self

    async def generate_image(self, folder: str) -> bytes:
        return await asyncio.to_thread(self._generate_image, os.path.join(folder, self.filename))

    def _generate_image(self, fp: str) -> bytes:
        with PIL.Image.open(fp) as img:
            self._image = img
            self._draw = ImageDraw(img)
            self.set_message(self.commit_repo.extra.message)
            self.set_time(self.commit_repo.extra.date)
            self.set_repository(self.commit_repo.repo.name)
            byte = io.BytesIO()
            img.save(byte, format="PNG")

        byte.seek(0)
        return byte.read()

    def get_message_position(self) -> Position:
        return Position(x=462, y=53, width=132, height=35)

    def get_repo_position(self) -> Position:
        return Position(x=527, y=124, width=66, height=21)

    def get_time_position(self) -> Position:
        return Position(x=527, y=96, width=66, height=21)

    def set_text_multiline(self, pos: Position, message: str) -> None:
        lines = textwrap.wrap(message, width=15)
        y_text = pos.y
        for i, line in enumerate(lines):
            width, height = self.font.getsize(line)
            if i == 1 and len(lines) > 2:
                line += '...'
            self._draw.text(((pos.width - width) / 2 + pos.x, y_text), line, font=self.font)
            y_text += height
            if i == 1:
                break

    def set_message(self, message: str) -> None:
        pos = self.get_message_position()
        self.set_text_multiline(pos, message)

    def set_time(self, date: datetime.datetime) -> None:
        pos = self.get_time_position()
        delta = humanize.naturaldelta(datetime.datetime.utcnow() - date)
        self.resize_fit(pos, delta)

    def resize_fit(self, pos: Position, message: str) -> None:
        current_font = self.font.size
        while True:
            font = self.create_font(current_font)
            width = self._draw.textlength(message, font=font)
            if width <= pos.width - self.padding:
                break

            current_font -= 1

        width, height = font.getsize(message)
        padding = self.padding - 3
        x = ((pos.width - width) / 2 + pos.x) - padding
        y = ((pos.height - height) / 2 + pos.y) - padding

        self._draw.text((x, y), message, font=font)

    def set_repository(self, repo_name: str) -> None:
        pos = self.get_repo_position()
        self.resize_fit(pos, repo_name)


class ImageHandler:
    directory: str = 'assets'

    def __init__(self) -> None:
        self.github: Optional[StellaGithub] = None
        self.cached_image: Optional[bytes] = None

    async def cleanup(self) -> None:
        if self.github:
            await self.github.cleanup()

    async def _generate_banner(self) -> bytes:
        value = await self.github.find_latest_all_commit()
        image = CommitAwareImage.load(self.directory, value)
        return await image.generate_image(self.directory)

    async def generate_banner(self) -> bytes:
        if not self.github.has_update():
            return self.cached_image

        self.cached_image = _bytes = await self._generate_banner()
        return _bytes

    async def acquire_github(self) -> None:
        if not self.github:
            github = await StellaGithub.init()
            self.github = github
