class MyClass:
    pass


def func1():
    pass


def func2():
    pass


a = b = func1

b()

a = b = func2


class MyClass:
    pass


def func1():
    pass


b = a = func1

a()
