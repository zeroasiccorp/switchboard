import pytest


@pytest.fixture(params=(0, 1, 2))
def sb_umi_ready_mode(request):
    return request.param


@pytest.fixture(params=(0, 1, 2))
def sb_umi_valid_mode(request):
    return request.param
