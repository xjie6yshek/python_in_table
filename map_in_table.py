import asyncio
import logging
import os
import webbrowser
import socket
import re

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


def inner(branch: NodeWrapper, items, root_url: URL, ):
    an_item = dict(link=str(root_url.update_query('&nodeid=' + branch.body.id)),
                   head=str(first_line(branch.body.properties.global_.title)),
                   node_type=str(branch.body.type_id))
    items.append(an_item)
    for child in branch.body.children:
        inner(child, items, root_url)


def print_tree(m: NodeWrapper, root_url: URL, ):
    items = []

    inner(m, items, root_url)
    html_string = open("templates/index.html", encoding="UTF-8").read()
    template = Template(html_string)

    with open("table.html", "w", encoding="UTF-8") as f:
        f.write(template.render(items=items))
    webbrowser.open('file://' + os.path.realpath("table.html"))


async def map_in_table(user_name: str, user_password: str, root_url: URL):
    map_id = root_url.query.get('mapid')
    node_id = root_url.query.get('nodeid')
    async with RfApiClient(
            auth=UserAuth(user_name, user_password),
    ) as api_client:
        m = await api_client.maps.get_map_nodes(map_id, node_id)
        print_tree(m, root_url)


regexEmail = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
regexURL = re.compile(r'https://')


def server_program():
    host = socket.gethostname()
    port = 5050
    server_socket = socket.socket()
    server_socket.bind((host, port))
    server_socket.listen(1)
    conn, address = server_socket.accept()
    user_name = ''
    user_password = ''
    url = ''
    print("Connection from: " + str(address))
    while True:
        data = conn.recv(1024).decode()
        print(str(data))
        if not data:
            break

        if str(data) == "user":
            if user_name == '':
                data = 'None'
            else:
                data = user_name

        elif str(data) == "password":
            if user_password == '':
                data = 'None'
            else:
                data = user_password

        elif str(data) == "url":
            if str(url) == '':
                data = 'None'
            else:
                data = str(url)

        elif re.fullmatch(regexEmail, str(data)):
            user_name = str(data)
            data = "user"
        elif re.search(regexURL, str(data)):
            url = str(data)
            data = "url"
        else:
            user_password = str(data)
            data = "pas"
        print("from connected user: " + str(data))

        if (user_name != '') and (user_password != '') and (url != ''):
            try:
                data += '\nLog in'
                loop = asyncio.get_event_loop()
                loop.run_until_complete(map_in_table(user_name, user_password, URL(url)))
                user_name = ''
                user_password = ''
                url = ''
                loop.close()
            except Exception:
                data += "\nlogin error"
                user_name = ''
                user_password = ''
                url = ''
        conn.send(data.encode())
    conn.close()


if __name__ == '__main__':
    server_program()
