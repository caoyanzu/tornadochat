# -*- coding:utf-8 -*-
import tornado.ioloop
import tornado.web
import tornado.options
import os.path
import tornado.escape
import uuid
import datetime
import logging
import tornado.websocket

from tornado.options import define,options

define('port',default = 8888,help = 'run on the given port',type = int)

class Application(tornado.web.Application):   #tornado应用类
    
    def __init__(self):
        handlers = [             #url映射
            (r'/',MainHandler),
            (r'/chatsocket',ChatSocketHandler),
        ]

        settings = dict(        #配置初始参数
            cookie_secret = 'shuo_caoyanzu_zuishuai',
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
        )

        super(Application, self).__init__(handlers, **settings) #调用父类构造函数

class MainHandler(tornado.web.RequestHandler):   #主页处理器
    
    def get(self):                               #get响应函数
        self.render("index.html",messages = ChatSocketHandler.cache,clients = ChatSocketHandler.waiters,username = '游客%d' % ChatSocketHandler.client_id)

class ChatSocketHandler(tornado.websocket.WebSocketHandler):
    waiters = set()             #保存所有在线websocket连接
    cache = []
    cache_size = 200
    client_id = 0

    def get_compression_options(self):
        return {}

    def open(self):             #websocket建立时调用
        #ChatSocketHandler.waiters.add(self)
        self.client_id = ChatSocketHandler.client_id
        ChatSocketHandler.client_id = ChatSocketHandler.client_id + 1
        self.username = '游客%d' %self.client_id
        ChatSocketHandler.waiters.add(self)

        chat = {
        'id' : str(uuid.uuid4()),
        'type' : 'online',
        'client_id' : self.client_id,
        'username' : self.username,
        'datetime' : datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        ChatSocketHandler.send_updates(chat)

    def on_close(self):         #websocket断开连接后调用
        ChatSocketHandler.waiters.remove(self)
        chat = {
            'id' : str(uuid.uuid4()),
            'type' : 'offline',
            'client_id' : self.client_id,
            'username' : self.username,
            'datetime' : datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        ChatSocketHandler.send_updates(chat)

    def on_message(self,message):   #收到websocket消息时调用
        logging.info('got message %r',message)
        parsed = tornado.escape.json_decode(message)
        self.username = parsed['username']
        chat = {
        'id' : str(uuid.uuid4()),
        'body' : parsed['body'],
        'type' : 'message',
        'client_id' : self.client_id,
        'username' : self.username,
        'datetime' : datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        chat['html'] = tornado.escape.to_basestring(self.render_string('message.html',message = chat))

        ChatSocketHandler.update_cache(chat)
        ChatSocketHandler.send_updates(chat)

    @classmethod
    def update_cache(cls,chat):   #增加缓存
        cls.cache.append(chat)
        if len(cls.cache) > cls.cache_size:
            cls.cache = cls.cache[-cls.cache_size:]

    @classmethod
    def send_updates(cls,chat):   #向所有客户端发送聊天消息
        logging.info('sending message to %d waiters',len(cls.waiters))
        for waiter in cls.waiters:
            try:
                waiter.write_message(chat)
            except:
                logging.error('error send message',exc_info = True)


def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()      #启动IOloop

if __name__ =='__main__':
    main()
