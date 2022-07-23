import asyncio
import logging
import os
import webbrowser

from jinja2 import Template
from yarl import URL

from rf_api_client import RfApiClient
from rf_api_client.rf_api_client import UserAuth
from rf_client.tree_wrapper import NodeWrapper

logging.basicConfig(level=logging.INFO)


def first_line(title: str) -> str:
    try:
        return title.strip().splitlines()[0].strip()
    except IndexError:
        return ''


def print_tree(m: NodeWrapper, url: URL,
               ):
    def inner(branch: NodeWrapper, items, url: URL,
              ):
        an_item = dict(link=str(url.update_query('&nodeid=' + branch.body.id)),
                       contenteditable=branch.body.meta.editable,
                       head=str(first_line(branch.body.properties.global_.title)),
                       node_type=str(branch.body.type_id))
        items.append(an_item)
        for child in branch.body.children:
            inner(child, items, url)

    items = []

    inner(m, items, url)
    html_string = open("templates/index.html").read()
    template = Template(html_string)

    with open("table.html", "w") as f:
        f.write(template.render(items=items))
    webbrowser.open('file://' + os.path.realpath("table.html"))


async def map_in_table():
    print('Username:', end=' ')
    username = input()

    print('Password:', end=' ')
    password = input()

    print('Link on root:', end=' ')
    url = URL(input())

    map_id = url.query.get('mapid')
    node_id = url.query.get('nodeid')
    async with RfApiClient(
        auth=UserAuth(username, password),
    ) as api_client:
        m = await api_client.maps.get_map_nodes(map_id, node_id)
        print_tree(m, url)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(map_in_table())
    loop.close()
