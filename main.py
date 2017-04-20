#!/usr/bin/env python
# -*- coding: utf-8 -*-

import functools
import re

import shortuuid
import web
from peewee import CharField, IntegerField, Model, SqliteDatabase

host = "10.67.13.145"
port = 8080
host_port = "http://{0}:{1}/".format(host, port)
short_header = host_port + "short/{0}"

DB_FILE = "short.db"
DB = SqliteDatabase(DB_FILE)

urls = (
    '/short/(.+)', 'redirect',
    '/', 'index',
)

class Short(Model):
    uuid = CharField()
    url = CharField()
    count = IntegerField()

    class Meta:
        database = DB

def check_and_create_tables():
    DB.connect()
    if not Short.table_exists():
        DB.create_tables([Short])


def html(content):
    return u"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <title>短链服务</title>
    </head>
    <body>
    """+ content + u"""
    </body>
    </html>
    """

def get_url(uuid):
    short = Short.select().where(Short.uuid == uuid)
    if len(short):
        return short[0].url
    else:
        return None

def get_uuid(url):
    short = Short.select().where(Short.url == url)
    if len(short):
        return short[0].uuid
    else:
        return None

def gen_uuid():
    uuid = shortuuid.ShortUUID().random(length=10)
    while get_url(uuid):
        uuid = shortuuid.ShortUUID().random(length=10)
    return uuid

def write_url(url, uuid):
    assert not get_url(uuid)
    Short.create(uuid=uuid, url=url, count=0).save()

def add_count(uuid):
    short = Short.select().where(Short.uuid == uuid)
    if len(short):
        short = short[0]
        short.count += 1
        short.save()

def use_db(f):
    @functools.wraps(f)
    def func(*args, **kwargs):
        DB.connect()
        f_return = f(*args, **kwargs)
        DB.close()
        return f_return
    return func


class index:
    @use_db
    def GET(self):
        request_data = web.input()
        if "url" in request_data:
            # 先判断url是否合法
            url_re = re.compile(r'(http://|https://|ftp://).*')
            if not url_re.match(request_data["url"]):
                return html(u"url不合法")
            if len(request_data["url"]) > 8182:
                return html(u"url太长")
            # 判断uuid是否存在
            uuid = get_uuid(request_data["url"])
            if uuid:
                return html(u"该url已有短链：<a href='{0}' target='_blank'>{0}</a>".format(short_header.format(uuid)))
            # 如果自定义uuid，则需要关心是否能用
            if "uuid" in request_data:
                uuid = request_data.get("uuid")
                if len(uuid) > 15:
                    return html(u"uuid太长")
                uuid_re = re.compile(r'[a-zA-Z0-9]+')
                if not uuid_re.match(uuid):
                    return html(u"uuid只能包含字母和数字")
                if get_url(uuid):
                    return html(u"该短链已被使用")
            if not uuid:
                uuid = gen_uuid()
            write_url(request_data["url"], uuid)
            return html(u"您的短链已生成：<a href='{0}' target='_blank'>{0}</a>".format(short_header.format(uuid)))
        else:
            html_content = u"<p>短链服务!<p>请在地址栏输入: {0}<p>支持自定义短链: {1}".format(host_port + u"?url=您的url", host_port + u"?url=您的url&uuid=您的uuid")
            return html(html_content)


class redirect:
    @use_db
    def GET(self, uuid):
        url = get_url(uuid)
        if url:
            add_count(uuid)
            web.seeother(url, absolute=True)
        else:
            return html(u"错误的短链接！")


if __name__ == "__main__":
    check_and_create_tables()
    app = web.application(urls, globals())
    web.httpserver.runsimple(app.wsgifunc(), (host, port))
