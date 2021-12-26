from contextlib import contextmanager

@contextmanager
def patch(obj_to_patch, attr, val):
    try:
        oldval = getattr(obj_to_patch, attr)
        setattr(obj_to_patch, attr, val)
        yield
    finally:
        setattr(obj_to_patch, attr, oldval)
