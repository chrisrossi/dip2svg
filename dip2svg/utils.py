
def first(i):
    try:
        return next(iter(i))
    except StopIteration:
        return None
