# Flask Task Monitor
A flask plugin to monitor thread task

## How to use
### Install
To install from source, download the source code, then run this:
```bash
python setup.py install
```
Or install with pip:
```bash
pip install Flask-Task-Monitor
```
### Setup
Adding the extension to your Flask app is simple:
```python
from flask import Flask
from flask_monitor import Monitor
monitor = Monitor(config={
    'FLASK_MONITOR_PERIOD': 1
})
app = Flask(__name__)
monitor.init_app(app)

```
Add monitered task with database
```python
from flask_monitor import DBMonitor
from yourapplication import monitor

class DemoMonitorJob(DBMonitor):
    def __init__(self, a, b, c):
        super(DemoMonitorJob, self).__init__()
        pass

    @classmethod
    def redo(cls, *args, **kwargs):
        '''
        execute when your job is crashed
        '''
        pass

    @classmethod
    def roll_back(cls, *args, **kwargs):
        '''
        execute after redo when catch exception 
        '''
        pass

    def do(self, *args, **kwargs):
        '''your own job which needs to monitered
        '''
        pass

monitor.add_check_monitor(DemoMonitorJob)

```
### Your own monitor 
You can code your own monitor by redis, zookeeper, etcd and more
```python
from flask_monitor import BaseMonitorInterface
class YourMonitor(BaseMonitorInterface):
    def lock(self, *args, **kwargs):
        '''
        when called your do function
        '''
        pass
        
    def unlock(self, args, **kwargs):
        '''
        when your do function return
        '''
        pass

    @classmethod
    def check(cls, *args, **kwargs):
        '''
        your own check function:
        it will return to
            try:
                redo(list, dict)
            except Expection:
                rollback(list,dict)
        '''
        return list, dict
        
    @abstractmethod
    def do(self, *args, **kwargs):
        pass
    
    @classmethod
    @abstractmethod
    def redo(self, *args, **kwargs):
        pass
      
    @classmethod   
    @abstractmethod
    def rollback(self, *args, **kwargs):
        pass
```

