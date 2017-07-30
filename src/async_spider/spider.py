#!/usr/bin/env python3
import asyncio
import aiohttp
import json
import click

from collections import MutableSequence
from yarl import URL
from bs4 import BeautifulSoup


async def soupify(html):
    soup = BeautifulSoup(html, 'html.parser').find_all('a')
    soup = map(
        lambda el: el['href'].split('#')[0] if 'href' in el.attrs else None,
        soup
    )
    #  Use 'set' instead of 'list' to deduplicate
    return set(filter(lambda el: el, soup))


class Page(object):
    semaphore = None
    loop = None

    def __init__(self, url):
        assert isinstance(url, str)
        if any(map(lambda el: el is None, [self.semaphore, self.loop])):
            raise AttributeError("Initialize Class-wide variables!")
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

    async def extract(self):
        with (await self.semaphore):
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url) as resp:
                    data = await resp.text()
        self.index = await soupify(data)
        return self.index


class Domain(MutableSequence):
    def __init__(self, url_obj):
        assert isinstance(url_obj, URL)
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
        self._list[pos] = value

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
        # Filter egress URLs and cast results to URL objects
        next_tasks = filter(
            lambda el: el.host == self.domain.name or not el.is_absolute(),
            map(lambda el: URL(el), res)
        )
        # Fix relative URLs, re-filter with full paths :)
        next_tasks = set([
            el if el.is_absolute() else URL.join(self.domain.url, el)
            for el in next_tasks
        ])
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
    def __init__(self, loop, settings=False, concurrency=None, entries=None):
        if settings:
            with open('settings.json') as settings_file:
                self.settings = json.load(settings_file)
        else:
            self.settings = {'concurrency': concurrency, 'entries': entries}
        Page.semaphore = asyncio.Semaphore(self.settings['concurrency'])
        Page.loop = loop
        self.loop = loop

    async def start(self):
        entries = self.settings['entries']
        self.targets = [Target(entry) for entry in entries]
        tasks = [target.start() for target in self.targets]
        await asyncio.gather(*tasks)

    def dump(self):
        import jsonpickle
        crawl_dump = {
            eo['name']: [
                {'url': ei['url'], 'index': ei['index']['py/set']}
                for ei in eo['_list']
            ]
            for eo in map(
                lambda el: json.loads(jsonpickle.encode(el.domain)),
                self.targets
            )
        }
        return crawl_dump

    def graph(self):
        import networkx as nx
        data = self.dump()
        g = nx.DiGraph()
        for domain in data:
            for page in data[domain]:
                g.add_edge(domain, page['url'])
                for link in page['index']:
                    g.add_edge(page['url'], link)
        p = nx.nx_agraph.to_agraph(g)
        p.graph_attr.update(
            landscape='false', ranksep='3.0', fontcolor='white',
            bgcolor='#333333', label='ASSE - Async Spider => Graph Report'
        )
        p.node_attr.update(
            shape='hexagon', fontcolor='white', color='white', style='filled',
            fillcolor='#006699'
        )
        p.edge_attr.update(color='white')
        p.draw(path='ig1', format='png', prog='dot')


@click.command()
@click.option('-a', '--auto', 'settings', is_flag=True,
              help='Read entries and concurrency from file.')
@click.option('-c', '--concurrency', type=click.INT, default=10,
              help='Number of concurrent connections.')
@click.option('-e', '--entries', default='', multiple=True,
              help='Entry point to crawl. (Reusable flag)')
@click.option('-g', '--graph', is_flag=True, help='Export report in graph.')
@click.argument('out', type=click.File('w'), default='', required=False)
def main(settings, concurrency, entries, graph, out):
    loop = asyncio.get_event_loop()
    c = Crawler(loop, settings, concurrency, entries)
    loop.run_until_complete(c.start())
    if graph:
        c.graph()
    if out:
        click.echo(json.dumps(c.dump()), file=out)


if __name__ == '__main__':
    main()
