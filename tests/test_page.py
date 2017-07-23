import asyncio
import unittest
from nose.tools import raises, with_setup
from asset.spider import Page

a_url = "https://example.com"


class TestPage(unittest.TestCase):

    @raises(AssertionError)
    def test_init_validation_int(self):
        _ = Page(42)

    def test_init_validation_str(self):
        _ = Page(a_url)

    def test_eq_valid(self):
        p1 = Page(a_url)
        assert p1 == a_url
        p2 = Page(a_url)
        assert p1 == p2

    @raises(TypeError)
    def test_eq_invalid(self):
        p1 = Page(a_url)
        p1 == 42

    def test_ne_valid(self):
        b_url = "https://example.com/join"
        p1 = Page(a_url)
        assert p1 != b_url
        p2 = Page(b_url)
        assert p1 != p2

    @raises(TypeError)
    def test_ne_invalid(self):
        p1 = Page(a_url)
        p1 != 42

    def test_str(self):
        p1 = Page(a_url)
        assert str(p1) == a_url

    def test_len(self):
        p1 = Page(a_url)
        assert len(p1) == 0
        p1.index.append(42)
        assert len(p1) == 1

    def test_soupify(self):
        async def go():
            p1 = Page(a_url)
            body = """
                <a href=\"https://example.com\">yada</a>
                <a href=\"https://example.com/join\">yada</a>
                <a href=\"join\">yada</a>
                <a href=\"https://example.com/index\">yada</a>
                <a href=\"https://example.com/index#join\">yada</a>
                <a href=\"index#join\">yada</a>
                <a href=\"index#yada\">yada</a>
            """
            await p1.soupify(body)
            # This happens bc of relative paths; they are filtered in Target
            assert len(p1.index) == 5
        asyncio.get_event_loop().run_until_complete(go())
