import logging
import argparse
import os
import json
from pprint import pprint
import time
import hashlib
from baidupcsapi import PCS
from common.models import ModelBooks, BookStatus

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')


def func_list(args, pcs):
    res = pcs.list_files(args.folder)
    pprint(json.loads(res.text))


def parse_filename(path):
    filename = os.path.split(path)[-1]
    start = filename.rfind('-')
    end = filename.rfind('.')

    if start != -1 and end != -1:
        filename = filename[:start] + filename[end:]

    return filename


def upload_file(path, dest, pcs, filename=None):
    logging.info('Start, "{}" -> "{}"'.format(path, dest))

    filename = filename or parse_filename(path)

    with open(path, 'rb') as fp:
        fmd5 = hashlib.md5(fp.read())
    with open(path, 'rb') as fp:
        res = pcs.upload(dest, fp, filename)
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
    if args.loop:
        while True:
            book = ModelBooks.get_a_book(status=BookStatus.DOWNLOADED, next_status=BookStatus.UPLOADING)
            if not book:
                logging.info('Sleep, no available books to upload now')
                time.sleep(30)
                continue
            path = os.path.join(args.path, '{}.epub'.format(book.safari_book_id))
            try:
                upload_file(path, args.folder, pcs, filename='{}.epub'.format(book.title))
                status = BookStatus.DOWNLOADED
            except:
                status = BookStatus.UPLOADED
            ModelBooks.finish(book.safari_book_id, status=status)
    elif os.path.isdir(args.path):
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

upload_parser = subparsers.add_parser(
    'upload',
    help='upload file to Baidu',
)
upload_parser.set_defaults(func=func_upload)
upload_parser.add_argument(
    dest='path', nargs='?'
)
upload_parser.add_argument(
    '-f',
    '--folder',
    default='',
    help='Folder on Baidu',
)
upload_parser.add_argument(
    '-l',
    '--loop',
    help='Upload file from db',
    action="store_true"
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
