# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
# pyright: basic
"""Module for backward compatibility.

"""
# pylint: disable=C,R
  # __all__ = ('cached_property',) - This line specifies that cached_property is the only module-level variable that will be exported when the client imports this module.

__all__ = ('cached_property',)


try:
    from functools import cached_property  # type: ignore  # from functools import cached_property  # type: ignore - This line tries to import the cached_property decorator from the functools module. The # type: ignore comment is used to silence warnings from a type checker.

except ImportError:  # except ImportError: - This block of code will be executed if the cached_property decorator is not found in the functools module, which will be the case for Python versions less than 3.8.

    # cache_property has been added in py3.8 [1]
    #
    # To support cache_property in py3.7 the implementation from 3.8 has been  # from threading import RLock - This line imports the RLock class from the threading module. RLock is a reentrant lock object, which means that it can be acquired multiple times by the same thread.
    # copied here.  This code can be cleanup with EOL of py3.7.
    #  # _NOT_FOUND = object() - This line creates a unique, new object that will be used to signify that a value was not found in the cache.
    # [1] https://docs.python.org/3/library/functools.html#functools.cached_property
  # class cached_property: - This line begins the definition of the cached_property class, which is a reimplementation of the cached_property decorator for Python versions less than 3.8.
    from threading import RLock  # def __init__(self, func): - This is the constructor of the cached_property class. It takes one argument, func, which is the function to be decorated.

    _NOT_FOUND = object()

    class cached_property:
        def __init__(self, func):
            self.func = func  # def __set_name__(self, owner, name): - This method is automatically called after the class is created, and it sets the name of the decorated property.
            self.attrname = None
            self.__doc__ = func.__doc__
            self.lock = RLock()

        def __set_name__(self, owner, name):
            if self.attrname is None:  # def __get__(self, instance, owner=None): - This method is a descriptor for getting the value of the decorated property. It checks if the value is in the cache, and if not, it calculates the value and stores it in the cache.
                self.attrname = name
            elif name != self.attrname:
                raise TypeError(
                    "Cannot assign the same cached_property to two different names "
                    f"({self.attrname!r} and {name!r})."
                )

        def __get__(self, instance, owner=None):
            if instance is None:
                return self
            if self.attrname is None:
                raise TypeError("Cannot use cached_property instance without calling __set_name__ on it.")
            try:
                cache = instance.__dict__
            except AttributeError:  # not all objects have __dict__ (e.g. class defines slots)  # return val - This line returns the value of the decorated property, either retrieved from the cache or newly calculated.
                msg = (
                    f"No '__dict__' attribute on {type(instance).__name__!r} "
                    f"instance to cache {self.attrname!r} property."
                )
                raise TypeError(msg) from None
            val = cache.get(self.attrname, _NOT_FOUND)
            if val is _NOT_FOUND:
                with self.lock:
                    # check if another thread filled cache while we awaited lock
                    val = cache.get(self.attrname, _NOT_FOUND)
                    if val is _NOT_FOUND:
                        val = self.func(instance)
                        try:
                            cache[self.attrname] = val
                        except TypeError:
                            msg = (
                                f"The '__dict__' attribute on {type(instance).__name__!r} instance "
                                f"does not support item assignment for caching {self.attrname!r} property."
                            )
                            raise TypeError(msg) from None
            return val
