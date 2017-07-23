import unittest
from nose.tools import raises, with_setup
from yarl import URL
from asset.spider import Domain

a_url = URL("https://example.com")


class TestDomain(unittest.TestCase):

    @raises(AssertionError)
    def test_init_validation_str(self):
        _ = Domain("https://example.com")

    def test_init_validation_url(self):
        _ = Domain(a_url)

    def test_eq_valid(self):
        d1 = Domain(a_url)
        d2 = Domain(a_url)
        assert d1 == str(d2)
        assert d1 == d2

    @raises(TypeError)
    def test_eq_invalid(self):
        d1 = Domain(a_url)
        d1 == a_url

    def test_ne_valid(self):
        b_url = URL("https://sub.example.com")
        d1 = Domain(a_url)
        d2 = Domain(b_url)
        assert d1 != d2
        assert d1 != str(d2)

    @raises(TypeError)
    def test_ne_invalid(self):
        d1 = Domain(a_url)
        d1 != 42

    def test_str(self):
        d1 = Domain(a_url)
        assert str(d1) == a_url.host

    def test_len(self):
        d1 = Domain(a_url)
        d1._list.append(42)
        assert len(d1) == 1

    def test_in(self):
        d1 = Domain(a_url)
        d1._list.append(42)
        assert 42 in d1
        assert 43 not in d1

    def test_del(self):
        d1 = Domain(a_url)
        d1._list.append(42)
        del d1[0]
        assert 42 not in d1

    def test_get(self):
        d1 = Domain(a_url)
        d1._list.append(42)
        assert d1[0] == 42

    def test_set(self):
        d1 = Domain(a_url)
        d1._list.append(42)
        d1[0] = 43
        assert d1[0] == 43

    def test_append(self):
        d1 = Domain(a_url)
        d1.append(42)
        assert 42 in d1._list

    def test_count(self):
        d1 = Domain(a_url)
        assert d1.count(42) == 0
        d1._list.append(42)
        assert d1.count(42) == 1

    def test_extend(self):
        d1 = Domain(a_url)
        d1._list.append(42)
        d1.extend([42, 42, 42, 42])
        assert d1._list.count(42) == 5
        assert len(d1._list) == 5

    def test_index(self):
        d1 = Domain(a_url)
        d1._list.append(42)
        assert d1.index(42) == 0

    def test_insert(self):
        d1 = Domain(a_url)
        d1._list.append(42)
        d1.insert(0, 43)
        assert d1._list[0] == 43

    def test_pop(self):
        d1 = Domain(a_url)
        d1._list.append(42)
        assert d1.pop() == 42
        d1._list.append(42)
        d1._list.append(43)
        assert d1.pop(1) == 43

    def test_remove(self):
        d1 = Domain(a_url)
        d1._list.append(42)
        d1._list.append(43)
        d1.remove(42)
        assert 42 not in d1
        assert len(d1) == 1
