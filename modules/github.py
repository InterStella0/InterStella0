from __future__ import annotations
import dataclasses
import datetime
import json
import operator
import traceback
from typing import Optional, Dict, Tuple

import aiofiles
from aiogithub import GitHub
from aiogithub.objects import User, Repo, Commit

from modules.errors import CommitMissing


class StellaGithub:
    update: datetime.timedelta = datetime.timedelta(minutes=10)

    def __init__(self):
        self.github_client: Optional[GitHub] = None
        self.repositories: dict[int, Repo] = {}
        self.author: Optional[User] = None
        self._last_update: Optional[datetime.datetime] = None

    @classmethod
    async def init(cls):
        github = cls()
        await github.initiate_github()
        return github

    def has_update(self) -> bool:
        now = datetime.datetime.now()
        if self._last_update and self._last_update + self.update > now:
            return False

        self._last_update = now
        return True

    async def cleanup(self):
        if self.github_client:
            await self.github_client.close()

    async def initiate_github(self):
        async with aiofiles.open('config.json') as r:
            config = json.loads(await r.read())
            self.github_client = client = GitHub(config['github_token'])

        self.author = user = await client.get_user(config['username'])
        self.repositories = {repo.id: repo async for repo in user.get_repos()}

    async def find_latest_commit(self, repo: Repo) -> Tuple[Commit, CommitCommitter]:
        async for commit in repo.get_commits():
            if commit.author.id != self.author.id:
                continue

            extra_author = CommitCommitter.from_dict(commit.commit)
            return commit, extra_author

        raise CommitMissing(f"Unable to find `{self.author.login}` commit in this repository.")

    async def find_latest_all_commit(self) -> RepoCommit:
        commits = []
        for repo in self.repositories.values():
            try:
                commit, extra = await self.find_latest_commit(repo)
            except Exception as e:
                traceback.print_tb(e)
            else:
                commits.append(RepoCommit(commit, extra, repo))

        if not commits:
            raise CommitMissing("No commit detected.")

        return max(commits, key=operator.attrgetter('extra.date'))


@dataclasses.dataclass
class CommitCommitter:
    name: str
    email: str
    date: datetime.datetime
    message: str

    @classmethod
    def from_dict(cls, values: Dict[str, str]):
        author = values['author']
        date = datetime.datetime.strptime(author['date'], "%Y-%m-%dT%H:%M:%SZ")
        return cls(author['name'], author['email'], date, values['message'])


@dataclasses.dataclass
class RepoCommit:
    commit: Commit
    extra: CommitCommitter
    repo: Repo
