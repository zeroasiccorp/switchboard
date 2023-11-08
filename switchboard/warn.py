# Infrastructure for printing deprecation warnings
# Copyright (C) 2023 Zero ASIC


import warnings


warnings.simplefilter('once', FutureWarning)


def warn_future(msg: str):
    warnings.warn(msg, category=FutureWarning)
