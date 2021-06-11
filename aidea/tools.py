#  Copyright 2021 Industrial Technology Research Institute
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import os
import sys
import json
import shutil
import functools
from getpass import getpass
from pathlib import Path
from typing import Optional, Tuple
from tqdm.auto import tqdm
from requests import get, post
from texttable import Texttable


WEBSITE_URL = 'https://aidea-web.tw'
API_SERVER_BASE_URL = f'{WEBSITE_URL}/api/v1'
CONFIG_FOLDER = '.aidea'
CONFIG_FILENAME = 'config.txt'


def login(*args, **kwargs) -> None:
    print('Please enter the following information.')
    username = input('username or email: ')
    password = getpass('password: ')
    url = f'{API_SERVER_BASE_URL}/login'
    try:
        result = post(
            url=url,
            data=json.dumps({
                'username': username,
                'password': password,
            }),
        )
    except Exception as e:
        print(e)

    if result.status_code == 200:
        print('Login OK.')
        jwt_content = result.json()['token']
        home = Path.home()
        path = home / CONFIG_FOLDER / CONFIG_FILENAME
        _write_jwt(jwt_content=jwt_content, path=path)
    else:
        print('Login failed. Please try again.')


def list_topics(*args, **kwargs) -> None:
    url = f'{API_SERVER_BASE_URL}/topics'
    try:
        result = get(
            headers=_get_customized_header(),
            url=url,
        )
    except Exception as e:
        print(e)

    if result.status_code == 403:
        print('Error happened. Please check the following reason.')
        print(' - Your login credentials may expire.')
    elif result.status_code == 200:
        topic_list = result.json()['topics']
    else:
        print(f'Status code = {result.status_code}')

    if result.status_code != 200:
        sys.exit(0)

    table = Texttable()
    table.set_cols_width([36, 48, 5, 7])
    table.set_deco(Texttable.HEADER)
    table.set_cols_dtype([
        't',  # text
        't',  # text
        'i',  # integer
        'a',  # automatic
    ])
    table.set_cols_align([
        'l',
        'l',
        'r',
        'l',
    ])

    table_rows = list()
    table_rows.append([
        'ID', 'Title', 'Teams', 'Entered'
    ])
    for topic in topic_list:
        row = [
            topic['topic_id'],
            topic['title'],
            topic['team_count'],
            'Yes' if topic['is_entered'] else 'No',
        ]
        table_rows.append(row)
    table.add_rows(table_rows)
    print(table.draw())


def list_topic_files(*args, **kwargs) -> None:
    topic_id = kwargs['topic_id']
    url = f'{API_SERVER_BASE_URL}/topics/files/{topic_id}'
    try:
        result = get(
            headers=_get_customized_header(),
            url=url,
        )
    except Exception as e:
        print(e)

    if result.status_code == 403:
        print('Error happened. Please check the following reasons.')
        print(' - Your login credentials may expire.')
        print(' - Your do not register the topic yet.')
        print(' - Not in download period now.')
    elif result.status_code == 404:
        print('Topic ID error. Please check again.')
    elif result.status_code == 200:
        file_list = result.json()['files']
    else:
        print(f'Status code = {result.status_code}')

    if result.status_code != 200:
        sys.exit(0)

    table = Texttable()
    table.set_cols_width([36, 18, 33])
    table.set_deco(Texttable.HEADER)
    table.set_cols_dtype([
        't',  # text
        't',  # text
        't',  # text
    ])
    table.set_cols_align([
        'l',
        'r',
        'l',
    ])

    table_rows = list()
    table_rows.append([
        'Filename', 'Size', 'MD5',
    ])
    for file in file_list:
        row = [
            file['filename'],
            '{:,}'.format(int(file['size'])),
            file['md5'],
        ]
        table_rows.append(row)
    table.add_rows(table_rows)
    print(table.draw())


def download_topic_files(*args, **kwargs) -> None:
    token = _get_token()
    topic_id = kwargs['topic_id']
    url = f'{API_SERVER_BASE_URL}/topics/files/{topic_id}'
    try:
        result = get(
            headers=_get_customized_header(),
            url=url,
        )
    except Exception as e:
        print(e)

    if result.status_code == 200:
        file_list = result.json()['files']
    else:
        print(f'Status code = {result.status_code}')
        sys.exit(0)

    file_url_list = [f'{WEBSITE_URL}{file["link"]}' for file in file_list]
    for file_url in file_url_list:
        local_filename = file_url.split('___')[1]
        error_message = _download_file(file_url, local_filename, token)
        if error_message:
            print(error_message)


def submit_result(*args, **kwargs) -> None:
    topic_id = kwargs['topic_id']
    file_path = kwargs['file_path']
    local_file_path = Path(file_path).expanduser().resolve()

    if not local_file_path.exists():
        print(f'Your file "{file_path}" does not exist. Please check again!')
        sys.exit(0)

    files = {
        'submission': open(local_file_path, 'rb')
    }
    url = f'{API_SERVER_BASE_URL}/topics/submission/{topic_id}'
    try:
        result = post(
            headers=_get_customized_header(),
            url=url,
            files=files,
        )
    except Exception as e:
        print(e)

    if result.status_code == 400:
        print('Error happened. Please check the following reasons.')
        print(' - (Edge AI) Only one concurrent submission is allowed.')
        print(' - You reached upload limits.')
    elif result.status_code == 403:
        print('Error happened. Please check the following reasons.')
        print(' - Your login credentials may expire.')
        print(' - Your do not register the topic yet.')
        print(' - Not in upload period now.')
    elif result.status_code == 404:
        print('Topic ID error. Please check again.')
    elif result.status_code == 200:
        print('Submit file OK.')
    else:
        print(f'Status code = {result.status_code}')

    if result.status_code != 200:
        sys.exit(0)


def _write_jwt(jwt_content: str, path: Path) -> None:
    try:
        os.makedirs(path.parent, exist_ok=True)
        path.write_text(jwt_content)
    except Exception as e:
        print(e)


def _read_jwt(path: Path) -> Tuple[Optional[str], Optional[str]]:
    error_msg = None
    jwt_content = None
    try:
        jwt_content = path.read_text()
    except Exception as e:
        error_msg = str(e)

    return jwt_content, error_msg


def _get_customized_header() -> Optional[dict]:
    home = Path.home()
    path = home / CONFIG_FOLDER / CONFIG_FILENAME
    if not path.exists():
        print('Please login first.')
        sys.exit(0)

    jwt_content, error_msg = _read_jwt(path)
    if error_msg:
        print('Please login first.')
        sys.exit(0)

    headers = {'Authorization': 'Bearer {}'.format(jwt_content)}

    return headers


def _get_token() -> Optional[dict]:
    home = Path.home()
    path = home / CONFIG_FOLDER / CONFIG_FILENAME
    if not path.exists():
        print('Please login first.')
        sys.exit(0)

    jwt_content, error_msg = _read_jwt(path)
    if error_msg:
        print('Please login first.')
        sys.exit(0)

    return jwt_content


def _download_file(url: str, local_filename: Path, token: str) -> None:
    error_message = None
    try:
        path = Path(local_filename).expanduser().resolve()
        if path.exists():
            ans = ''
            while ans == '':
                ans = input(f'File "{local_filename}" exists. Continue and overwrite? (Y/N) ').strip()
                if ans == '':
                    continue

                if ans.lower() != 'y':
                    error_message = f'Skip file "{local_filename}"'
                    return error_message
                else:
                    break

        path.parent.mkdir(parents=True, exist_ok=True)

        cookie = f'JWT={token}'
        from requests.auth import HTTPBasicAuth
        r = get(url,
                stream=True,
                allow_redirects=True,
                headers={'cookie': cookie},
                )
        if r.status_code != 200:
            r.raise_for_status()
            raise RuntimeError(f'Request to {url}, status code = {r.status_code}')
        file_size = int(r.headers.get('Content-Length', 0))

        desc = '(Unknown file size)' if file_size == 0 else ''
        r.raw.read = functools.partial(r.raw.read, decode_content=True)
        with tqdm.wrapattr(r.raw, 'read', total=file_size, desc=desc) as r_raw:
            with path.open('wb') as f:
                shutil.copyfileobj(r_raw, f)
    except Exception as e:
        error_message = f'Can not download file {url}'

    return error_message
