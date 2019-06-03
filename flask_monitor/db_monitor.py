import os
import json
import datetime
import functools
import time
import random
from .base import BaseMonitorInterface
from abc import abstractmethod
from sqlalchemy import create_engine, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

db_url = os.getenv('SQLALCHEMY_DATABASE_URI', '')
engine = create_engine(db_url, pool_recycle=60)
Base = declarative_base()


class Muti_Lock(Base):
    __tablename__ = "sync_lock_table"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    update_time = Column(DateTime)

    def __init__(self, name, time):
        self.name = name
        self.update_time = time


def sync_lock_decorator(name):
    """Decorator to handle with request timeout"""

    def _lock():
        lock = Muti_Lock(name, datetime.datetime.now())
        try:
            s.add(lock)
            s.commit()
        except Exception:
            s.rollback()
            # clear timeout lock
            time.sleep(random.randint(1, 10))
            locks = s.query(Muti_Lock).filter_by(name=name).all()
            for lock in locks:
                delta = datetime.datetime.now() - lock.update_time
                if delta.seconds > 600:
                    s.delete(lock)
            try:
                s.commit()
            except Exception:
                s.rollback()
            return None
        return lock

    def _unlock():
        locks = s.query(Muti_Lock).filter_by(name=name).all()
        for lock in locks:
            s.delete(lock)
        s.commit()

    def _lock_decorator(func):
        @functools.wraps(func)
        def decorator(*args, **kwargs):
            # Enable the timer
            while True:
                lock = _lock()
                if lock is None:
                    time.sleep(10)
                else:
                    break
            res = func(*args, **kwargs)
            _unlock()
            return res

        return decorator

    return _lock_decorator


class Monitor_Lock(Base):
    __tablename__ = "monitor_lock_table"

    id = Column(Integer, primary_key=True)
    monitorname = Column(String(50))
    obj_config = Column(Text)
    args = Column(Text)
    kwargs = Column(Text)
    create_time = Column(DateTime)
    update_time = Column(DateTime, onupdate=datetime.datetime.now)

    def __init__(self, monitorname, args, kwargs, obj_config, create_time):
        self.monitorname = monitorname
        self.args = args
        self.kwargs = kwargs
        self.create_time = create_time
        self.obj_config = obj_config


# Create all the tables in the database which are
# defined by Base's subclasses such as User
Base.metadata.create_all(engine)

# Construct a sessionmaker factory object
session_factory = sessionmaker(bind=engine)

Session = scoped_session(session_factory)

# Generate a session to work with
s = Session()


class DBMonitor(BaseMonitorInterface):
    lock_timeout = int(os.getenv('FLASK_LOCK_TIMEOUT', '180'))

    def __init__(self):
        pass

    @abstractmethod
    def do(self, *args, **kwargs):
        pass

    def unlock(self, *args, **kwargs):
        id = kwargs.get('lock', None)
        lock = s.query(Monitor_Lock).filter_by(id=id).first()
        if lock is not None:
            s.delete(lock)
            try:
                s.commit()
            except Exception:
                s.rollback()

    def lock(self, *args, **kwargs):
        claz_name = kwargs.get('wrapped').__self__.__class__.__name__
        obj_config = kwargs.get('wrapped').__self__.__dict__
        args_dict = []
        kwargs_dict = {}
        object_dict = {}
        for value in args:
            if type(value) == list or type(value) == dict or type(value) == str or type(value) == float or type(
                    value) == bool or type(value) == int:
                args_dict.append(value)
        for key, value in kwargs.items():
            if type(value) == list or type(value) == dict or type(value) == str or type(value) == float or type(
                    value) == bool or type(value) == int:
                kwargs_dict[key] = value

        for key, value in obj_config.items():
            if type(value) == list or type(value) == dict or type(value) == str or type(value) == float or type(
                    value) == bool or type(value) == int:
                object_dict[key] = value

        lock_insert = Monitor_Lock(
            monitorname=claz_name,
            obj_config=json.dumps(object_dict),
            args=json.dumps(args_dict),
            kwargs=json.dumps(kwargs_dict),
            create_time=datetime.datetime.now()
        )
        s.add(lock_insert)
        try:
            s.commit()
        except Exception:
            s.rollback()
        return lock_insert.id

    @classmethod
    @abstractmethod
    def roll_back(cls, *args, **kwargs):
        pass

    @classmethod
    @sync_lock_decorator("dbmonitor")
    def check(cls, *args, **kwargs):
        locks = s.query(Monitor_Lock).filter_by(monitorname=cls.__name__).all()
        redo_list = []
        for lock in locks:
            delta = datetime.datetime.now() - lock.create_time
            if delta.seconds > cls.lock_timeout:
                # need to redo or rallback
                redo_list.append({
                    'monitorname': lock.monitorname,
                    'use_time': str(delta),
                    'kwargs': json.loads(lock.kwargs),
                    'args': json.loads(lock.args),
                    'object': json.loads(lock.obj_config)
                })
                s.delete(lock)
        s.commit()
        return redo_list, {}

    @classmethod
    @abstractmethod
    def redo(cls, *args, **kwargs):
        pass
