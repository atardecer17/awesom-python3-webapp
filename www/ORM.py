#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 12 09:38:47 2017

@author: atardecer
"""
import asyncio, logging
import aiomysql

def log(sql, args=()):
    logging.info('SQL: %s' % (sql))

def create_args_string(num):
    return ','.join(['?' for i in range(num)])    
    
    
@asyncio.coroutine
def create_pool(loop, **kw):
    logging.info('create database connection pool')
    global __pool
    __pool = yield from aiomysql.create_pool(
            host = kw.get('host', 'localhost'),
            port = kw.get('port', 3306),
            user = kw['user'],
            password = kw['password'],
            db = kw['db'],
            charset = kw.get('charset', 'utf8'),
            autocommit = kw.get('autocommit', True),
            maxsize = kw.get('maxsize', 10),
            minsize = kw.get('minsize', 1),
            loop = loop
            )


@asyncio.coroutine
def select(sql, args, size=None):
    log(sql, args)
    global __pool
    with (yield from __pool) as conn:
        cur = yield from conn.cursor(aiomysql.DictCursor)
        yield from cur.execute(sql.replace('?', '%s'), args or ())
        if size:
            rs = yield from cur.fetchmany(size)
        else:
            rs = yield from cur.fetchall()
        yield from cur.close()
        logging.info('row returned %s' % len(rs))
        return rs

@asyncio.coroutine
def execute(sql, args):
    log(sql)
    with (yield from __pool) as conn:
        try:        
            cur = yield from conn.cursor()
            yield from cur.execute(sql.replace('?', '%s'), args)
            affected = cur.rowcount
            yield from cur.close()
        except BaseException as e:
            raise
        return affected
    


class Field(object):
    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default
        
        
    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__,self.column_type, self.name)
    
    
class StringField(Field):
    def __init__(self, name=None, column_type='varchar(100)', primary_key=False, default=None):
        super(StringField, self).__init__(name, column_type, primary_key, default)
    
    
class IntegerField(Field):
    def __init__(self, name=None, primarykey=False, default=0, column_type='bigint'):
        super(IntegerField, self).__init__(name, column_type, primarykey, default)
        
class BooleanField(Field):
    def __init__(self, name=None, default=False):
        super(BooleanField, self).__init__(name,'boolean', False, default)

class FloatField(Field):
    def __init__(self, name=None, primary_key=False, default=0.0):
        super(FloatField, self).__init__(name, 'real', primary_key, default)
        
class TextField(Field):
    def __init__(self, name=None, default=None):
        super(TextField, self).__init__(name, 'Text', False, default)
        
class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
        tablename = attrs.get('__table__', None) or name
        logging.info('Found model: %s(table: %s)' % (name, tablename))
        mappings = {}
        fields = []
        primarykey = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                logging.info('Found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                if v.primary_key:
                    if primarykey:
                        raise RuntimeError('Duplicate primary key for field: %s' %k )
                    primarykey = k
                else:
                    fields.append(k)
        
        if not primarykey:
            raise RuntimeError('primary key not found...')
        for k in mappings.keys():
            attrs.pop(k)
        #`` is same as repr()
        escaped_fields = list(map(lambda f: '`%s`' % f, fields))
        
        attrs['__mappings__'] = mappings
        attrs['__table__'] = tablename
        attrs['__primary_key__'] = primarykey
        attrs['__fields__'] = fields
        attrs['__select__'] = 'SELECT `%s`, %s FROM `%s`' % (primarykey, ','.join(escaped_fields), tablename)
        attrs['__insert__'] = 'INSERT INTO `%s`(%s,`%s`) VALUES(%s)' %(tablename, ','.join(escaped_fields), primarykey,  create_args_string(len(escaped_fields)+1))
        attrs['__update__'] = 'UPDATE `%s` SET %s WHERE `%s`=?' % (tablename, '.'.join(map(lambda f: '`%s`=?' %(mappings.get(f).name or f), fields)), primarykey)
        attrs['__delete__'] = 'DELETE FROM `%s` where `%s=?`' % (tablename, primarykey)
        
        return type.__new__(cls, name, bases, attrs)

class Model(dict, metaclass=ModelMetaclass):
    def __init__(self, **kw):
        super(Model, self).__init__(**kw)
        
    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError:
            raise AttributeError(r"'Model' object don't have attribute %s " % k)
            
    def __setattr__(self, key, value):
        self[key] = value
        
    def getValueorDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value
    
    @classmethod
    @asyncio.coroutine
    def find(cls, pk):
        rs = yield from select('%s WHERE `%s`=?' %(cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])
        
    @asyncio.coroutine
    def save(self):
        args = list(map(self.getValueorDefault, self.__fields__))
        args.append(self.getValueorDefault(self.__primary_key__))
        rows = yield from execute(self.__insert__, args)
        if rows != 1:
            logging.warn('failed to insert into record: affeced rows: %s!' % rows)
    
        