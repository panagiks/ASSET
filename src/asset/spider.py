#!/usr/bin/env python3
import asyncio
import aiohttp
import json

from collections import MutableSequence
from yarl import URL
from bs4 import BeautifulSoup


class Page(object):
    semaphore = None
    loop = None

    def __init__(self, url):
        assert isinstance(url, str)
        self.url = url
        self.index = []

    def __eq__(self, other):
        if isinstance(other, Page):
            return self.url == other.url
        elif isinstance(other, str):
            return self.url == other
        else:
            raise TypeError("Can't compare apples to oranges")

    def __ne__(self, other):
        if isinstance(other, Page):
            return self.url != other.url
        elif isinstance(other, str):
            return self.url != other
        else:
            raise TypeError("Can't compare apples to oranges")

    def __repr__(self):
        return "<{} object: {}>".format(self.__class__.__name__, self.url)

    def __str__(self):
        return self.url

    def __len__(self):
        return len(self.index)

    def __iter__(self):
        for url in self.index:
            yield url

    async def dump(self):
        """
        Dump Pages links. Decide whether to use db or file.
        """
        print(self.url)
        for el in self.index:
            print("\t", el)

    async def soupify(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        soup = filter(lambda el: 'href' in el.attrs, soup.find_all('a'))
        soup = [link['href'] for link in soup]
        self.index = list(filter(lambda el: not el.startswith('#'), soup))

    async def extract(self):
        if any(map(lambda el: el is None, [Page.semaphore, Page.loop])):
            raise UnboundLocalError("Initialize Class-wide variables!")
        with (await Page.semaphore):
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url) as resp:
                    data = await resp.text()
        await self.soupify(data)
        await self.dump()
        return self.index


class Domain(MutableSequence):
    def __init__(self, url_obj):
        super().__init__()
        self.object = url_obj
        self.name = url_obj.host
        self.url = url_obj.origin()
        self._list = list()

    def __eq__(self, other):
        if isinstance(other, Domain):
            return self.name == other.name
        elif isinstance(other, str):
            return self.name == other
        else:
            raise TypeError("Can't compare apples to oranges")

    def __ne__(self, other):
        if isinstance(other, Domain):
            return self.name != other.name
        elif isinstance(other, str):
            return self.name != other
        else:
            raise TypeError("Can't compare apples to oranges")

    def __repr__(self):
        return "<{} object: {}\n{}>".format(
            self.__class__.__name__, self.name, self._list
        )

    def __str__(self):
        return self.name

    def __len__(self):
        return len(self._list)

    def __contains__(self, element):
        return element in self._list

    def __delitem__(self, item):
        del self._list[item]

    def __getitem__(self, pos):
        return self._list[pos]

    def __setitem__(self, pos, value):
        self._list.key[pos] = value

    def append(self, value):
        return self._list.append(value)

    def count(self, value):
        return self._list.count(value)

    def extend(self, iterable):
        return self._list.extend(iterable)

    def index(self, value, *args):
        return self._list.index(value, *args)

    def insert(self, index, value):
        return self._list.insert(index, value)

    def pop(self, *args):
        return self._list.pop(*args)

    def remove(self, value):
        return self._list.remove(value)


class Target(object):
    def __init__(self, entry):
        self.url = URL(entry)
        self.entry = Page(entry)
        self.domain = Domain(self.url)

    async def start(self):
        await self.crawl(self.entry)

    async def crawl(self, entry):
        if entry not in self.domain:
            self.domain.append(entry)
        res = await entry.extract()
        # Filter egress URLs and cast resulrs to URL objects
        next_tasks = filter(
            lambda el: el.host == self.domain.name or not el.is_absolute(),
            map(lambda el: URL(el), res)
        )
        # Fix relative URLs
        next_tasks = [
            el if el.is_absolute() else URL.join(self.domain.url, el)
            for el in next_tasks
        ]
        # Remove non HTTP/HTTPS entries ... we won't be using the tel: proto :p
        next_tasks = filter(
            lambda el: el.scheme in ["http", "https"], next_tasks
        )
        # Remove already crawled URLs and cast
        next_tasks = filter(
            lambda el: el not in self.domain,
            map(lambda el: Page(el.human_repr()), next_tasks)
        )
        tasks = [self.crawl(task) for task in next_tasks]
        await asyncio.gather(*tasks)


class Crawler(object):
    def __init__(self, loop):
        with open('settings.json') as settings_file:
            self.settings = json.load(settings_file)
        Page.semaphore = asyncio.Semaphore(self.settings['concurrency'])
        Page.loop = loop
        self.loop = loop

    async def start(self):
        entries = self.settings['entries']
        targets = [Target(entry) for entry in entries]
        tasks = [target.start() for target in targets]
        await asyncio.gather(*tasks)


loop = asyncio.get_event_loop()
c = Crawler(loop)
loop.run_until_complete(c.start())
