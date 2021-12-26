import sys

# fun with python decorators and reflection to add method overloading
def overload(func):
    def wrapper(self, *args, **kwargs):
        return getattr(
            sys.modules[self.__module__],
            f'__{self.__class__.__name__}_{func.__name__}_{len(args) + 1}'
        )(self, *args, **kwargs)

    module = sys.modules[func.__module__]
    name = f'__{repr(func)[10:].split(".")[0]}_{func.__name__}_{func.__code__.co_argcount}'

    if hasattr(module, name):
        raise ValueError(f'{func.__module__} already has an attribute {name}')

    setattr(module, name, func)
    return wrapper
