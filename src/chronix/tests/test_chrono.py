from chronix import FlexTimer


def test_basic_package_smoke():
    timer = FlexTimer(start_now=False)
    assert isinstance(timer, FlexTimer)
