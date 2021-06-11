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

import argparse
from . import tools


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-v',
                        '--version',
                        action='version',
                        version='AIdea CLI 1.0.0')

    subparsers = parser.add_subparsers(title='commands',
                                       dest='command')
    subparsers.required = True
    add_login_parser(subparsers)
    add_topics_parser(subparsers)
    args = parser.parse_args()

    command_args = {}
    command_args.update(vars(args))
    command_args.pop('func')
    command_args.pop('command')
    args.func(**command_args)


def add_login_parser(subparsers):
    login_parser = subparsers.add_parser('login', aliases=['l'])
    login_parser.set_defaults(func=tools.login)


def add_topics_parser(subparsers):
    topics_parser = subparsers.add_parser('topics', aliases=['t'])
    topics_subparsers = topics_parser.add_subparsers(title='commands',
                                                     dest='command')
    topics_subparsers.required = True

    # list
    topics_list_parser = topics_subparsers.add_parser('list')
    topics_list_parser.add_argument(
        '-c',
        '--category',
        dest='category',
        required=False,
        metavar='<category>',
    )
    topics_list_parser.set_defaults(func=tools.list_topics)

    # files
    topics_files_parser = topics_subparsers.add_parser('files')
    topics_files_parser.add_argument(
        '-t',
        '--topic_id',
        dest='topic_id',
        required=True,
        metavar='<topic_id>',
    )
    topics_files_parser.set_defaults(func=tools.list_topic_files)

    # download
    topics_download_parser = topics_subparsers.add_parser('download')
    topics_download_parser.add_argument(
        '-t',
        '--topic_id',
        dest='topic_id',
        required=True,
        metavar='<topic_id>',
    )
    topics_download_parser.set_defaults(func=tools.download_topic_files)

    # submit
    topics_submit_parser = topics_subparsers.add_parser('submit')
    topics_submit_parser.add_argument(
        '-t',
        '--topic_id',
        dest='topic_id',
        required=True,
        metavar='<topic_id>',
    )
    topics_submit_parser.add_argument(
        '-f',
        '--file',
        dest='file_path',
        required=True,
        metavar='<file_path>',
    )
    topics_submit_parser.set_defaults(func=tools.submit_result)


if __name__ == '__main__':
    main()
