def accepts(*classinfo_args):
    """Decorator to check types of property."""
    def isinstance_decorator_wrapper(old_fn):
        def new_fn(self, *args, **kwargs):
            for i, classinfo in enumerate(classinfo_args):
                arg = args[i]
                if not isinstance(arg, classinfo):
                    if isinstance(classinfo, tuple):
                        obj_name = "', '".join([x.__name__ for x in classinfo])
                    else:
                        obj_name = " '" + classinfo.__name__
                    msg = "Attribute {} must be of type{}' but "\
                          "argument of type '{}' was given".format(
                            old_fn.__name__, "s '" + obj_name,
                            type(arg).__name__)
                    raise TypeError(msg)
            return old_fn(self, *args, **kwargs)
        return new_fn
    return isinstance_decorator_wrapper
