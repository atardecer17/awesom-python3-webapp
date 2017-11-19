#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 16 12:08:41 2017

@author: atardecer
"""

import ORM
from models import Users
import asyncio

def test(loop):
    yield from ORM.create_pool(loop=loop, user='www-data', password='www-data', db='awesome')
    sql = 'SELECT * FROM users'    
    rs = yield from ORM.select(sql, None) 
    print(rs)
    
loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait([test(loop)]))
