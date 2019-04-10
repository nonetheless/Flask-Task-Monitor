# Copyright (c) 2017 `Transwarp, Inc. <http://www.transwarp.io>`_.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Transwarp, Inc nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import logging
import types
import six
import wrapt
import time
from abc import ABCMeta, abstractmethod

logger = logging.getLogger(__name__)

__all__ = ['BaseMonitorInterface', 'MiniterDaemonSingleton', 'Monitor']


@wrapt.decorator
def monitor(wrapped, monitor, args, kwargs):
    """Decorator to process monitor do exceptions"""
    kwargs['wrapped'] = wrapped
    lock = monitor.lock(*args, **kwargs)
    kwargs['lock'] = lock
    wrapped(*args, **kwargs)
    monitor.unlock(*args, **kwargs)


class MonitorMetaClass(ABCMeta):
    """General catcher of DAO operations
    """

    def __new__(mcs, name, bases, kwargs):
        for m in kwargs:
            val = kwargs[m]
            is_routine = isinstance(val, classmethod) \
                         or isinstance(val, staticmethod) \
                         or isinstance(val, types.MethodType) \
                         or isinstance(val, types.FunctionType)
            if is_routine and m == "do":
                kwargs[m] = monitor(kwargs[m])
        return type.__new__(mcs, name, bases, kwargs)


class BaseMonitorInterface(six.with_metaclass(MonitorMetaClass)):
    """
    DAO interface with additional properties and error processing.
    """

    @abstractmethod
    def do(self, *args, **kwargs):
        pass

    @abstractmethod
    def lock(self, *args, **kwargs):
        pass

    @abstractmethod
    def unlock(self, *args, **kwargs):
        pass

    @classmethod
    @abstractmethod
    def roll_back(cls, *args, **kwargs):
        pass

    @classmethod
    @abstractmethod
    def check(cls, *args, **kwargs):
        pass

    @classmethod
    @abstractmethod
    def redo(cls, *args, **kwargs):
        pass


class SingletonMetaClass(type):
    """ A metaclass that creates a Singleton base class when called. """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMetaClass, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Singleton(SingletonMetaClass('SingletonMeta', (object,), {})):
    pass


class MiniterDaemonSingleton(Singleton):
    """
    A daemon mixin with singleton property.

    This daemon service can be configured with different number of workers.
    """

    def __init__(self, workers=1, process_pool=False):
        if process_pool:
            from concurrent.futures import ProcessPoolExecutor as PoolExecutor
            from multiprocessing import Manager
        else:
            from concurrent.futures import ThreadPoolExecutor as PoolExecutor
            from multiprocessing.dummy import Manager

        self.executor = PoolExecutor(max_workers=workers)
        self.worker = None
        self.manager = Manager()

    def set_worker(self, fn, *args, **kwargs):
        """
        Set the worker function that will be submitted
        to the pool when starting.
        """
        self.worker = (fn, args, kwargs)

    def start(self):
        """
        Start the running pools with given worker.
        :return: a Future object.
        """
        fn, args, kwargs = self.worker
        return self.executor.submit(fn, *args, **kwargs)

    def stop(self, wait=True):
        """
        Call to stop the threading pool.
        """
        self.executor.shutdown(wait)


class Monitor(MiniterDaemonSingleton):
    def __init__(self, app=None, config=None):
        super(Monitor, self).__init__()
        self.app = None
        self.check_map = self.manager.dict()
        self.config = config

        if app is not None:
            self.init_app(app=app, config=config)

    def init_app(self, app, config=None):
        if self.config is not None:
            app.config['FLASK_MONITOR_PERIOD'] = self.config.get('FLASK_MONITOR_PERIOD', 180)
        if config is not None:
            app.config['FLASK_MONITOR_PERIOD'] = config.get('FLASK_MONITOR_PERIOD', 180)
        self.app = app

    def _worker(self, period):
        with self.app.app_context():
            while True:
                time.sleep(period)
                logger.info('Checking monitor ...')
                for key, value in self.check_map.items():
                    args = []
                    kwargs = {}
                    try:
                        args, kwargs = value.check()
                        value.redo(*args, **kwargs)
                    except Exception as e:
                        logger.warning(e)
                        value.rollback(*args, **kwargs)

    def add_check_monitor(self, claz: BaseMonitorInterface):
        self.check_map[type(claz).__name__] = claz.__class__

    def start(self):
        # Background thread handling with the configs refreshing
        logger.info('Starting the ha manager ...')
        self.set_worker(self._worker, period=self.app.config.get('FLASK_MONITOR_PERIOD', 1))
        super(Monitor, self).start()