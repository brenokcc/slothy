
def fieldset(dictionary):
    def decorate(func):
        metadata = getattr(func, '_metadata', {})
        fieldsets = {}
        for verbose_name, str_or_tuples in dictionary.items():
            fieldsets[verbose_name] = []
            if isinstance(str_or_tuples, str):  # sigle field
                fieldsets[verbose_name].append((str_or_tuples,))
            else:  # multiple fields
                for str_or_tuple in str_or_tuples:
                    if isinstance(str_or_tuple, str):  # string
                        fieldsets[verbose_name].append((str_or_tuple,))
                    else:  # tuple
                        fieldsets[verbose_name].append(str_or_tuple)

        metadata.update(
            fieldsets=fieldsets
        )
        setattr(func, '_metadata', metadata)
        return func

    return decorate
