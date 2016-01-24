from direct.showbase.ShowBase import ShowBase
from direct.task import Task

def print_foo(task):
    print("foo")
    return Task.cont

s = ShowBase()
base.taskMgr.add(print_foo, "Print that foo each frame", sort = -100)
s.run()