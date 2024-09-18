"""Module with decorator to check types of property."""


def accepts(*classinfo_args):
    """Decorator to check types of property."""
    def isinstance_decorator_wrapper(old_fn):
        def new_fn(self, *args, **kwargs):
            for i, classinfo in enumerate(classinfo_args):
                arg = args[i]
                if not isinstance(arg, classinfo):
                    if isinstance(classinfo, tuple):
                        obj_type = "' or '".join([x.__name__ for x in classinfo])
                    else:
                        obj_type = classinfo.__name__
                    msg = f"Attribute {old_fn.__name__} must be of type "\
                          f"'{obj_type}' but '{type(arg).__name__}' was passed"
                    raise TypeError(msg)
            return old_fn(self, *args, **kwargs)
        return new_fn
    return isinstance_decorator_wrapper
