# -*- coding: utf-8 -*-

from slothy.admin import store


def shortcut(lookups=None, priority=0):
    def decorate(func):
        store('shortcut', func, lookups, priority)
        return func
    return decorate


def card(lookups=None, priority=0):
    def decorate(func):
        store('card', func, lookups, priority)
        return func
    return decorate


def top(lookups=None, priority=0, formatter=None):
    def decorate(func):
        store('top', func, lookups, priority, formatter)
        return func
    return decorate


def left(lookups=None, priority=0, formatter=None):
    def decorate(func):
        store('left', func, lookups, priority, formatter)
        return func
    return decorate


def center(lookups=None, priority=0, formatter=None):
    def decorate(func):
        store('center', func, lookups, priority, formatter)
        return func
    return decorate


def right(lookups=None, priority=0, formatter=None):
    def decorate(func):
        store('right', func, lookups, priority, formatter)
        return func
    return decorate


def bottom(lookups=None, priority=0, formatter=None):
    def decorate(func):
        store('bottom', func, lookups, priority, formatter)
        return func
    return decorate
