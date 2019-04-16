from flask_monitor import DBMonitor
from flask_monitor import Monitor
from flask import Flask


class HelloMonitor(DBMonitor):
    def __init__(self):
        super(HelloMonitor, self).__init__()
        self.hello = 'hello'

    def do(self, *args, **kwargs):
        print("do")

    def roll_back(self, *args, **kwargs):
        print("roll_back")


app = Flask(__name__)
app.config.update(
    FOO_BAR='baz',
    FOO_SPAM='eggs',
)

monitor = Monitor()
monitor.init_app(app)
monitor.start()

if __name__ == '__main__':
    hello = HelloMonitor()
    monitor.add_check_monitor(HelloMonitor)
    hello.do(cluster_id=1)
