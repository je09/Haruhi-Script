"""
Haruhi Script V. 0.9
je09 22.07.2019

A mangadex parser/downloader

Named after Haruhi Suzumiya
"""

import json
import re
from pathlib import Path
from sys import stdout, exit

import click
import requests


def get_manga_id(manga_path, base_url):
    manga_id = manga_path

    if base_url.format('') in manga_path:
        i = -1
        while int(len(manga_path.split('/'))/2) > -1*i:
            tmp = manga_path.strip(' ').split('/')[i]
            if tmp.isdigit():
                manga_id = tmp
                break
            i-=1

    if not manga_id.isdigit():
        exit('Invalid link or id')

    return manga_id


def get_manga_details(manga_id, base_url, headers):
    API_ENDPOINT = base_url.format('api/manga/{0}')
    r = requests.get(
        API_ENDPOINT.format(manga_id),
        headers=headers
    )

    details = r.json()

    if 'status' in details and details['status'] != 'OK':
        exit('Invalid manga id')

    meta = details['manga']
    click.echo('\nTitle: {0} \nDescription: {1} \nArtist: {2} \nAuthor: {3}\n'.format(
        meta['title'],
        meta['description'],
        meta['artist'],
        meta['author']
    ))

    return details['chapter'], meta['title']


def save_chapter(manga_id, path, base_url, headers):
    API_ENDPOINT = base_url.format('/api/?id={0}&type=chapter&baseURL=%2Fapi')
    r = requests.get(
        API_ENDPOINT.format(manga_id),
        headers=headers
    )

    data = r.json()

    manga_hash = data['hash']
    chapter = data['chapter']
    server = data['server']
    if server == '/data/':
        server = 'https://mangadex.org/data/'
    if not chapter:
        chapter = '1'

    path = '{0}/Chapter-{1}'.format(path, chapter)
    click.echo('\nDownloading chapter {0}'.format(chapter))

    exists = Path.exists(Path(path))

    if not exists:
        Path.mkdir(Path(path))
        for file_name in enumerate(data['page_array']):
            file_raw = requests.get(
                server + manga_hash + '/' + file_name[1],
                headers=headers
            )

            file_raw.raise_for_status()
            stdout.write('\r%d/%d' %(file_name[0] + 1, len(data['page_array'])))
            stdout.flush()

            with open(path + '/' + file_name[1], 'wb') as file:
                file.write(file_raw.content)

    if exists:
        click.echo('A folder with this chapter already exists. Skipping.', nl=False)


def write_config(config_path, path):
    path = '/' + path.strip('/')
    with open(config_path, 'w', encoding='utf-8') as config_file:
        config = json.dumps(
            {
                'path': path
            }
        )
        config_file.writelines(config)


def make_save_dir(lang, title, default_name):
    CONFIG_PATH = str(Path.home()) + '/.haruhi'

    title = title.replace(' ', '_').lower()

    path = str(Path.home()) + '/' + default_name

    if Path.exists(Path(CONFIG_PATH)):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as config_file:
            config = json.loads(
                ''.join(config_file.readlines())
            )
        path = config['path']
        del config
    else:
        write_config(CONFIG_PATH, path)

    new_path = input('Default saving-path is {0}' 
                     '\nTo change it type new here: '.format(path))
    if new_path:
        path = new_path
        write_config(CONFIG_PATH, path)

    path += '/' + title + '-' + lang
    Path.mkdir(Path(path), parents=True, exist_ok=True)

    return path


def find_chapters(lang, data, title, default_name, base_url, headers):
    click.echo('Trying to find chapters with a "{0}" language code'.format(lang))
    result = False
    for _, chapter in data.items():
        if chapter['lang_code'] == lang:
            result = True
            break

    click.echo('Result: {0}'.format(result))
    if result:
        path = make_save_dir(lang, title, default_name)
        manga_list = []
        for manga_id, chapter in data.items():
            if chapter['lang_code'] == lang:
                manga_list.append(manga_id)
        del data

        for i in range(len(manga_list)-1, 0, -1):
                save_chapter(manga_list[i], path, base_url, headers)
                click.echo()
        del manga_list


def print_version(ctx, _, value):
    VERSION = '0.9'

    if not value or ctx.resilient_parsing:
        return
    click.echo('Haruhi-Script version {0}'.format(VERSION))
    ctx.exit()


@click.command()
@click.option(
    '-m',
    '--manga',
    prompt='Input URL of the manga or it\'s ID',
    type=str,
    help='URL of the manga or it\'s ID on mangadex.\n'
         'Example: "https://mangadex.org/title/30123/internet-explorer" '
         'or "30123"'
)
@click.option(
    '-l',
    '--language',
    prompt='Input language of the manga',
    type=str,
    help='Language of the manga. '
         'Language should be represented in language code format.\n'
         'Example: gb, fr, ru'
)
@click.option(
    '-v',
    '--version',
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
    help='Show version of the haruhi-script'
)
def main(manga, language):
    DEFAULT_NAME = 'haruhi' # Name for a default folder
    BASE_URL = 'https://mangadex.org/{0}' # url of a site to parse to
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/60.0.3112.113 Safari/537.36'
    }

    pattern = re.compile('^[a-z]{2}$') # 2 letter codes only
    if not re.match(pattern, language):
        exit('Invalid language code format')

    manga_id = get_manga_id(manga, BASE_URL)
    details, title = get_manga_details(manga_id, BASE_URL, HEADERS)
    find_chapters(
        language,
        details,
        title,
        DEFAULT_NAME,
        BASE_URL,
        HEADERS
    )
    click.echo('\nDone!')


if __name__ == '__main__':
    try:
        main()
    except requests.exceptions.ConnectionError:
        click.echo('Check your internet connection')