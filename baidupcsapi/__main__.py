import logging
import argparse
import os
import json
from pprint import pprint
import hashlib

from application.api import PCS

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')


def func_list(args, pcs):
    res = pcs.list_files(args.folder)
    pprint(json.loads(res.text))


def upload_file(path, dest, pcs):
    file_name = os.path.split(path)[-1]
    logging.info('Start, "{}" -> "{}"'.format(path, dest))

    start = file_name.rfind('-')
    end = file_name.rfind('.')

    if start != -1 and end != -1:
        file_name = file_name[:start] + file_name[end:]

    with open(path, 'rb') as fp:
        fmd5 = hashlib.md5(fp.read())
    with open(path, 'rb') as fp:
        res = pcs.upload(dest, fp, file_name)
        data = json.loads(res.text)
        """
        {'ctime': 1531534213,
         'fs_id': 115394279740290,
         'isdir': 0,
         'md5': '85f0be30e17e696a4dbd312f5f412ff7',
         'mtime': 1531534213,
         'path': '//README.md',
         'request_id': 4509236039960989015,
         'size': 13}
        """
        pprint(data)
        md5 = data['md5']
        if md5 == fmd5.hexdigest():
            os.remove(path)
            logging.info('Finish, "{}" -> "{}"'.format(path, dest))
        else:
            logging.error('Fail, "{}" -> "{}"'.format(path, dest))


def upload_folder(folder, dest, pcs):
    for i in os.listdir(folder):
        path = os.path.join(folder, i)
        if os.path.isdir(path):
            upload_folder(path, dest, pcs)
        else:
            upload_file(path, dest, pcs)


def func_upload(args, pcs):
    if os.path.isdir(args.path):
        upload_folder(args.path, args.folder, pcs)
    else:
        upload_file(args.path, args.folder, pcs)


parser = argparse.ArgumentParser(
    description='Crawl Safari Books Online book content',
)
parser.add_argument(
    '-u',
    '--username',
    help='Baidu user / e-mail address',
)
parser.add_argument(
    '-p',
    '--password',
    help='Baidu password',
)
parser.add_argument(
    '-c',
    '--cookie',
    default='',
    help='Baidu cookie',
)

subparsers = parser.add_subparsers()

download_parser = subparsers.add_parser(
    'upload',
    help='upload file to Baidu',
)
download_parser.set_defaults(func=func_upload)
download_parser.add_argument(
    dest='path', nargs='?'
)
download_parser.add_argument(
    '-f',
    '--folder',
    default='',
    help='Folder on Baidu',
)

list_parser = subparsers.add_parser(
    'list',
    help='List folder',
)
list_parser.add_argument(dest='folder', nargs='?')
list_parser.set_defaults(func=func_list)


def main():
    args = parser.parse_args()
    pcs = PCS(username=args.username, password=args.password, cookie=args.cookie)
    args.func(args, pcs)


if __name__ == '__main__':
    main()
