#!/usr/bin/env python

import os
import click
import json
import requests
import discogs_client
from datetime import date
from prettytable import PrettyTable

@click.group()
def cli():
    pass

@click.command()
@click.option('-u', '--user-token', default=lambda: os.getenv('BOT_TOKEN'), required=True, help='bot token')
def show(user_token):
    d = discogs_client.Client('cli/0.1', user_token=user_token)
    me = d.identity()
    table = PrettyTable()
    table.align = "l"
    table.field_names = ["artists", "title", "year", "date_added"]

    for item in me.collection_folders[0].releases:
        artists_list = [ i.name for i in item.release.artists ]
        artists = " ".join(artists_list)[:60]
        title = item.release.title[:60]
        table.add_row([artists, title, item.release.year, item.date_added])
    print(table.get_string(sortby="date_added"))


@click.command()
@click.option('-f', '--file-name', required=True, help='backup file')
def backup_show(file_name):
    with open(file_name, 'r') as f:
        bcp_data = f.read()

    table = PrettyTable()
    table.align = "l"
    table.field_names = ["artists", "title", "year", "date_added"]
    for release in json.loads(bcp_data)["releases"]:
        artists_list = [ i["name"] for i in release["basic_information"]["artists"] ]
        artists = " ".join(artists_list)[:60]
        title = release["basic_information"]["title"][:60]
        year = release["basic_information"]["year"]
        table.add_row([artists, title, year, release["date_added"]])
    print(table.get_string(sortby="date_added"))

@click.command()
@click.option('-u', '--user-token', default=lambda: os.getenv('BOT_TOKEN'), required=True, help='bot token')
@click.option('-f', '--file-name', required=True, help='backup file')
def restore(user_token, file_name):
    with open(file_name, 'r') as f:
        bcp_data = f.read()

    d = discogs_client.Client('cli/0.1', user_token=user_token)
    me = d.identity()
    collection = me.collection_folders[0]
    col_rel = [ i.id for i in collection.releases]
    for item in json.loads(bcp_data)["releases"]:
        if item["id"] in col_rel:
            click.secho(f"\"{item['basic_information']['title']}\" already in collection", fg="yellow")
        else:
            collection.add_release(item["id"])

@click.command()
@click.option('-u', '--user-name', required=True, help='user name')
@click.option('-f', '--file-name', default=None, help='backup file', show_default=False)
def backup(user_name, file_name):
    page = 0
    per_page = 10
    pages = 1
    url = f"https://api.discogs.com/users/{user_name}/collection/folders/0/releases"
    bak = {"pagination": {}, "releases": []}
    while page != pages:
        payload = {"page": page + 1, "per_page": per_page}
        r = requests.get(url, params=payload)
    
        if r.status_code != 200:
            click.secho(f"ERROR: {r.json()['message']}", fg="red")
            exit (1)
    
        res = r.json()
        pages = res["pagination"]["pages"]
        page = res["pagination"]["page"]
        bak["releases"] += res["releases"]
    
    bak["pagination"] = {'page': page, 'pages': pages,
                        'per_page': per_page,
                        'items': res["pagination"]["items"], 'urls': {}}

    file_name = file_name if file_name else f"discogs_{user_name}-{date.today()}.json"
    with open(file_name, "w") as f:
        f.write(json.dumps(bak))
    click.secho(f"Backup successfully saved to {file_name}", fg="green")

cli.add_command(show)
cli.add_command(backup)
cli.add_command(backup_show)
cli.add_command(restore)

if __name__ == '__main__':
    cli()
