# Infrastructure for printing deprecation warnings

# Copyright (c) 2024 Zero ASIC Corporation
# This code is licensed under Apache License 2.0 (see LICENSE for details)


import warnings


warnings.simplefilter('once', FutureWarning)


def warn_future(msg: str):
    warnings.warn(msg, category=FutureWarning)
