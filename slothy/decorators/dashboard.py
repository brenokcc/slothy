
DATA = dict()


def setdata(key, func, lookups, priority, formatter=None):
    if key not in DATA:
        DATA[key] = []
    DATA[key].append(
        dict(func=func, lookups=lookups, priority=priority, formatter=formatter)
    )


def shortcut(lookups=None, priority=0):
    def decorate(func):
        setdata('shortcut', func, lookups, priority)
        return func
    return decorate


def card(lookups=None, priority=0):
    def decorate(func):
        setdata('card', func, lookups, priority)
        return func
    return decorate


def top(lookups=None, priority=0, formatter=None):
    def decorate(func):
        setdata('top', func, lookups, priority, formatter)
        return func
    return decorate


def left(lookups=None, priority=0, formatter=None):
    def decorate(func):
        setdata('left', func, lookups, priority, formatter)
        return func
    return decorate


def center(lookups=None, priority=0, formatter=None):
    def decorate(func):
        setdata('center', func, lookups, priority, formatter)
        return func
    return decorate


def right(lookups=None, priority=0, formatter=None):
    def decorate(func):
        setdata('right', func, lookups, priority, formatter)
        return func
    return decorate


def bottom(lookups=None, priority=0, formatter=None):
    def decorate(func):
        setdata('bottom', func, lookups, priority, formatter)
        return func
    return decorate


def top_bar(lookups=None, priority=0):
    def decorate(func):
        setdata('top_bar', func, lookups, priority)
        return func
    return decorate


def bottom_bar(lookups=None, priority=0):
    def decorate(func):
        setdata('bottom_bar', func, lookups, priority)
        return func
    return decorate


def floating(lookups=None, priority=0):
    def decorate(func):
        setdata('floating', func, lookups, priority)
        return func
    return decorate


def calendar(lookups=None, priority=0):
    def decorate(func):
        setdata('calendar', func, lookups, priority)
        return func
    return decorate


def public(priority=0):
    def decorate(func):
        setdata('public', func, (), priority)
        return func
    return decorate
