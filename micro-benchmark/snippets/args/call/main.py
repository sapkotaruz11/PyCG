class MyClass:
    def param_func(c, d):
        h = c
        k = d


def func(a):
    a()


x = 10
y = 20
z = MyClass()
z.param_func(x, y)
x = 1.0
y = 2.0

z.param_func(x, y)
