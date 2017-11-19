#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov 18 10:53:04 2017

@author: atardecer
"""


'''
use the web frame could be conviented to programing 

it contain Handler_decorator, RequestHandler and add_routes

'''
import functools, inspect
from urllib import parse
import asyncio, logging
from aiohttp import web
from apis import APIError






def Handler_decorator(path, *, method):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = method
        wrapper.__route__ = path
        return wrapper
    return decorator

get = functools.partial(Handler_decorator, method='GET')
post = functools.partial(Handler_decorator, method='POST')

#POSITIONAL_ONLY      position args
#KEYWORD_ONLY         mingming key word
#VAR_POSITIONNAL      *args
#VAR_KEYWORD          **kw
#POSITIONAL_OR_KEYWORD  positonal or required args

# get the mingming key word args which don't have default
def get_requird_kw_args(fn):
    args = []
    
    ''''' 
    def foo(a, b = 10, *c, d,**kw): pass 
    sig = inspect.signature(foo) ==> <Signature (a, b=10, *c, d, **kw)> 
    sig.parameters ==>  mappingproxy(OrderedDict([('a', <Parameter "a">), ...])) 
    sig.parameters.items() ==> odict_items([('a', <Parameter "a">), ...)]) 
    sig.parameters.values() ==>  odict_values([<Parameter "a">, ...]) 
    sig.parameters.keys() ==>  odict_keys(['a', 'b', 'c', 'd', 'kw']) 
    ''' 
    
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty:
            args.append(name)
    return tuple(args)

# get the mingming key word args
def get_named_kw_args(fn):
    args = []
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            args.append(name)
    return tuple(args)

# judge contain mingming key word args or not
def has_name_kw_arg(fn):
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            return True
        
# judge contain key word args or not
def has_var_kw_arg(fn):
    params = inspect.signature(fn).parameters
    for name, param inparams.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True
        
# judge contain the 'request' arg and it is in the last
def has_request_arg(fn):
    params = inspect.signature(fn).parameters
    found = False
    sig = inspect.signature(fn)
    for name, param in params.items():
        if name = 'request':
            found = True
            continue
        if found and (
                param.kind != inspect.Parameter.VAR_POSITIONAL and
                param.kind != inspect.Parameter.KEYWORD_ONLY and
                param.kind != inspect.Parameter.VAR_KEYWORD):
            # if param is positional arg 
            raise ValueError('request parameter must be the last named parameter in function:%s%s') % (fn__name__, str(sig))
    return found



'''
RequestHandler需要处理以下问题：
1、确定HTTP请求的方法（’POST’or’GET’）（用request.method获取）
2、根据HTTP请求的content_type字段，选用不同解析方法获取参数。（用request.content_type获取）
3、将获取的参数经处理，使其完全符合视图函数接收的参数形式
4、调用视图函数
'''

'''
GET、POST方法的参数必需是KEYWORD_ONLY
URL参数是POSITIONAL_OR_KEYWORD
REQUEST参数要位于最后一个POSITIONAL_OR_KEYWORD之后的任何地方
'''

class RequestHandler:
    def __init__(self, app, fn):
        self._app = app
        self._fn = fn
        self._required_kw_args = get_required_kw_args(fn)
        self._named_kw_args = get_named_kw_args(fn)
        self._has_request_arg = has_requset_arg(fn)
        self._has_named_kw_arg = has_named_kw_arg(fn)
        self._has_var_kw_arg = has_var_arg(fn)
        
    # 1.定义kw，用于保存参数  
    # 2.判断视图函数是否存在关键词参数，如果存在根据POST或者GET方法将request请求内容保存到kw  
    # 3.如果kw为空（说明request无请求内容），则将match_info列表里的资源映射给kw；若不为空，把命名关键词参数内容给kw  
    # 4.完善_has_request_arg和_required_kw_args属性  
    
    # request args(get, post...args)
    async def __call__(self, request):
        kw = None
        if self._has_named_kw_arg or self._has_var_kw_arg:
            if request.method = 'POST':
                if request.content_type = None:
                    return web.HTTPBadRequest(text='Missing Content_Type.')
                ct = request.content_type.lower()
                if ct.startwith('application/json'):
                    params = await request.json()
                    if not isinstance(params, dict):
                        return web.HTTPBadRequest(text='JSON body must be object.')
                    kw = params
                if ct.startwith(('application/x-www-form-urlencoded', 'multipart/form-data')):
                    params = await request.post
                    kw = dict(**params)
                else:
                    return web.HTTPBadRequest(text='Unsupported Content-Type: %s' % request.context_type)
            
            if request.method = 'GET':
                qs = request.query_string
                if qs:
                    kw = dict()
                    for k, v in parse.parse_qs(qs, True).items:
                        kw[k] = v[0]

        # match_info args(url args)
        if kw is None:
            kw = dict(**requset.match_info)
        else:
            if self._has_named_kw_arg and (not self._has_var_kw_arg):
                copy = {}
                for name in self._named_kw_arg:
                    if name in kw:
                        copy[name] = kw[name]
                kw = copy
            for k, v in request.match_info.items():
                if k in kw:
                    logging.warn('Duplicate arg name in request args: %s' % k)
                kw[k] = 
                
        # request 
        if self._has_request_arg:
            kw['request'] = request
        
        # check named args dont have defaut
        if self._required_kw_args:
            for name in self._required_kw_args:
                if not name in kw:
                    return web.HTTPBadRequest(text='Missing Argument %s' % name)
        
        logging.info('call with args: %s' % str(kw))
        
        try:
            r  await self._func(**kw)
            return r
        except APIerror as e:
            return dict(error=e.error, data=e.data, message=e.message)
        
        
              
def add_static(app):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.router.add_static('/static/', path)
    logging.info('add static %s => %s' % ('/static/', path))
    
def add_route(app, fn):
    method = getattr(fn, '__method__', None)
    path = getattr(fn, '__path__', None)
    if path is None or method is None:
        raise ValueError('@get or @post not defined in %s' % str(fn))
    # a little can't understand
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn = asyncio.coroutine(fn)
    logging.info('add route %s %s => %s(%s)' % (method, path, fn.__name__, ', '.join(inspect.signature(fn).paramethers.keys())))
    app.router.add_route(method, path, RequestHandler(app, fn))

def add_routes(app, module_name):
    n = module_name.rfind('.')
    if n == (-1):
        mod = __import__(module_name, globals(), locals())
    else:
        name = module_name[n+1:]
        mod = getattr(__import__(module_name[:n], globals(), locals(), [name]), name)
    for attr in dir(mod):
        if attr.startwith('_'):
            continue
        fn = getattr(mod, attr)
        if callable(fn):
            method = getattr(fn, '__method__', None)
            path = getattr(fn, '__route__', None)
            if method and path:
                add_route(app, fn)
                
        
        





                    
                    
                    
                    
                    
                    
                    
                    
                    

    
    
    
    
    
    
    
    