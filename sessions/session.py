# -*- coding: utf-8 -*-
import asyncio
import warnings
from aiohttp import TCPConnector, ClientSession, ClientTimeout, ClientResponse


# Classi interne
#from exceptions import SessionNotCreatedException, SessionAlreadyCreatedException


class MyHttp:
    """ Classe per gestire chiamate http """

    warnings.filterwarnings('ignore', message='Unverified HTTPS request')
    timeout = ClientTimeout(total=30)

    def __init__(self, headers: dict):
        self.session = None
        self.headers = headers
        self.semaphore = asyncio.Semaphore(3)

    async def __aenter__(self):
        self.session = ClientSession(timeout=self.timeout, connector=TCPConnector(verify_ssl=False, limit=1),
                                     headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.session:
            await self.session.close()

    def get_session(self):
        return self.session

    async def get(self, url: str) -> ClientResponse:
        """
        if not self.session:
            raise SessionNotCreatedException
        """

        return await self.session.get(url)
