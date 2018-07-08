import codecs
import json
import os
import re
import shutil
import tempfile
from functools import partial

import scrapy
# from scrapy.shell import inspect_response
from jinja2 import Template
from bs4 import BeautifulSoup

from ..db_session import SESSION, with_transaction
from ..models import ModelBooks
from .. import utils

DEFAULT_STYLE = """
p.pre {
  font-family: monospace;
  white-space: pre;
}"""

PAGE_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
    <head>
        <title></title>
        <style>
        {{style}}
        </style>
    </head>
    {{body}}
</html>"""


# def url_base(u):
#   # Actually I can use urlparse, but don't want to fall into the trap of py2 py3
#   # Does this code actually support py3?
#   try:
#     idx = u.rindex('/')
#   except:
#     idx = len(u)
#   return u[:idx]

def decode(s):
    try:
        return s.decode("utf8")
    except:
        return s

class SafariBooksSpider(scrapy.spiders.Spider):
    search_url = 'https://www.safaribooksonline.com/api/v2/search/'
    toc_url = 'https://www.safaribooksonline.com/nest/epub/toc/?book_id='
    name = 'SafariBooks'
    # allowed_domains = []
    start_urls = ['https://www.safaribooksonline.com/']
    host = 'https://www.safaribooksonline.com/'

    def __init__(
        self,
        user,
        password,
        cookie,
        bookid,
        output_directory=None,
        query=None
    ):
        self.user = user
        self.query = query
        self.password = password
        self.cookie = cookie
        self.bookid = str(bookid)
        self.output_directory = utils.mkdirp(
            output_directory or tempfile.mkdtemp()
        )
        self.book_name = ''
        self.epub_path = ''
        self.style = ''
        self.info = {}
        self._stage_toc = False
        self.tmpdir = tempfile.mkdtemp()
        self._initialize_tempdir()
        self._books_dict = {}
        self._scraped_books = 0

    def _initialize_tempdir(self):
        self.logger.info(
            'Using `{0}` as temporary directory'.format(self.tmpdir)
        )

        # `copytree` doesn't like when the target directory already exists.
        os.rmdir(self.tmpdir)

        shutil.copytree(utils.pkg_path('data/'), self.tmpdir)

    def parse(self, response):
        if self.cookie is not None:
            cookies = dict(x.strip().split('=') for x in self.cookie.split(';'))

            return scrapy.Request(url=self.host + 'home',
                callback=self.after_login,
                cookies=cookies,
                headers={
                    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36'
                })

        return scrapy.FormRequest.from_response(
              response,
              formdata={'email': self.user, 'password1': self.password},
              callback=self.after_login
        )

    def after_login(self, response):
        # Loose rule to decide if user signed in successfully.
        if response.status == 401:
            self.logger.error('Failed login')
            return
        elif response.status != 200:
            self.logger.error('Something went wrong')
            return

        self.query = 'mining data'
        if self.query:
            sort_by_score = "report_score"
            sort_by_relevance = "relevance"
            post_body = {
                "query": self.query,
                "extended_publisher_data": "true",
                "highlight": "true",
                "is_academic_institution_account": "false",
                "source": "user",
                "include_assessments": "false",
                "include_case_studies": "true",
                "include_courses": "true",
                "include_orioles": "true",
                "include_playlists": "true",
                "formats": ["book"],
                "topics": [],
                "publishers": [],
                "languages": [],
                "sort": sort_by_score,
                "page": 0
            }
            yield scrapy.Request(
                self.search_url,
                method='POST',
                body=json.dumps(post_body),
                callback=partial(self.query_books, post_body),
                headers={"content-type": "application/json"}
            )
        else:
            yield scrapy.Request(
                self.toc_url + self.bookid,
                callback=self.parse_toc,
            )

    @with_transaction
    def save_books_in_db(self, books_dict):
        models = []
        for book in books_dict.values():
            models.append(ModelBooks(
                safari_book_id=int(book['archive_id']),
                reviews=book.get('number_of_reviews', 0),
                rating=book.get('average_rating', 0),
                popularity=book.get('popularity', 0),
                report_score=book.get('report_score', 0),
                pages=book.get('virtual_pages', 0),
                title=book.get('title', ''),
                language=book.get('language', ''),
                authors=book.get('authors', []),
                publishers=book.get('publishers', []),
                tag=[self.query],
                description=book.get('description', ''),
                url=book.get('url', ''),
                web_url=book.get('web_url', ''),
            ))

        SESSION.add_all(models)
        SESSION.flush()

    def query_books(self, post_body, response):
        response = json.loads(response.body)
        total_books = response['total']
        self._scraped_books += len(response['results'])
        for book in response['results']:
            self._books_dict[book['archive_id']] = book
        print(total_books, len(self._books_dict))
        if self._scraped_books < total_books:
            post_body['page'] += 1
            yield scrapy.Request(
                self.search_url,
                method='POST',
                body=json.dumps(post_body),
                callback=partial(self.query_books, post_body),
                headers={"content-type": "application/json"}
            )
        else:
            self.save_books_in_db(self._books_dict)

    def parse_cover_img(self, name, response):
        # inspect_response(response, self)
        cover_img_path = os.path.join(self.tmpdir, 'OEBPS', 'cover-image.jpg')
        with open(cover_img_path, 'wb') as fh:
            fh.write(response.body)

    def parse_content_img(self, img, response):
        img_path = os.path.join(os.path.join(self.tmpdir, 'OEBPS'), img)

        img_dir = os.path.dirname(img_path)
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)

        with open(img_path, 'wb') as fh:
            fh.write(response.body)

    def parse_page_json(self, title, bookid, response):
        page_json = json.loads(response.body)

        style_sheets = page_json.get('stylesheets', [])
        style_sheets_paths = []

        for style_sheet in style_sheets:
            style_sheets_paths.append(style_sheet['full_path'])
            yield scrapy.Request(
                style_sheet['url'], # I don't know when style_sheets will have multiple elements
                callback=partial(self.load_page_style, style_sheet['full_path'])
            )

        yield scrapy.Request(
            page_json['content'],
            callback=partial(
                self.parse_page,
                title,
                bookid,
                page_json['full_path'],
                page_json['images'],
                style_sheets_paths
            )
        )

    def load_page_style(self, full_path, response):
        # TODO: obviously the best approach is to create file for styles
        # and share them in the downloaded files. But you need to carefully calculates the relative path.
        # For now just append to self.style
        self.style += response.body

    def parse_page(self, title, bookid, path, images, style, response):
        template = Template(PAGE_TEMPLATE)

        # path might have nested directory
        dirs_to_make = os.path.join(
            self.tmpdir,
            'OEBPS',
            os.path.dirname(path),
        )
        if not os.path.exists(dirs_to_make):
            os.makedirs(dirs_to_make)

        oebps_body_path = os.path.join(self.tmpdir, 'OEBPS', path)
        with codecs.open(oebps_body_path, 'wb', 'utf-8') as fh:
            body = decode(str(BeautifulSoup(response.body, 'lxml').find('body')))
            style = self.style if self.style != '' else DEFAULT_STYLE
            style = decode(style)
            fh.write(template.render(body=body, style=style))

        for img in images:
            if not img:
                continue

            # fix for books which are one level down
            img = img.replace('../', '')

            yield scrapy.Request(
                '/'.join((self.host, 'library/view', title, bookid, img)),
                callback=partial(self.parse_content_img, img),
            )

    def parse_toc(self, response):
        try:
            toc = json.loads(response.body)
        except Exception:
            self.logger.error(
                'Failed evaluating toc body: {0}'.format(response.body),
            )
            return

        self._stage_toc = True

        self.book_name = toc['title_safe']
        self.book_title = re.sub(r'["%*/:<>?\\|~\s]', r'_', toc['title'])  # to be used for filename
        self.book_title = "".join([ch for ch in self.book_title if ord(ch) <= 128])

        cover_path, = re.match(
            r'<img src="(.*?)" alt.+',
            toc['thumbnail_tag'],
        ).groups()

        yield scrapy.Request(
            self.host + cover_path,
            callback=partial(self.parse_cover_img, 'cover-image'),
        )

        for item in toc['items']:
            yield scrapy.Request(
                self.host + item['url'],
                callback=partial(
                    self.parse_page_json,
                    toc['title_safe'],
                    toc['book_id'],
                ),
            )

        content_path = os.path.join(self.tmpdir, 'OEBPS', 'content.opf')
        with open(content_path) as fh:
            template = Template(fh.read())
        with codecs.open(content_path, 'wb', 'utf-8') as fh:
            fh.write(template.render(info=toc))

        toc_path = os.path.join(self.tmpdir, 'OEBPS', 'toc.ncx')
        with open(toc_path) as fh:
            template = Template(fh.read())
        with codecs.open(toc_path, 'wb', 'utf-8') as fh:
            fh.write(template.render(info=toc))

    def closed(self, reason):
        if self._stage_toc is False:
            self.logger.info(
                'Did not even got toc, ignore generated file operation.'
            )
            return

        zip_path = shutil.make_archive(self.book_name, 'zip', self.tmpdir)
        self.logger.info('Made archive {0}'.format(zip_path))

        self.epub_path = os.path.join(
            self.output_directory,
            '{0}-{1}.epub'.format(self.book_title, self.bookid),
        )
        self.logger.info('Moving {0} to {1}'.format(zip_path, self.epub_path))
        shutil.move(zip_path, self.epub_path)
