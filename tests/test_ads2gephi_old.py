import os
import pytest
import ads
from ads.sandbox import SearchQuery
import ads2gephi.ads2gephi as ads2gephi
from ads2gephi.ads2gephi import CitationNetwork

TEST_DATABASE_PATH = 'tests/ads2gephi_sqlite.db'


@pytest.fixture()
def citnet(request, monkeypatch):
    monkeypatch.setattr(ads2gephi, 'ads', ads.sandbox)
    citnet = CitationNetwork(TEST_DATABASE_PATH)
    ads.config.token = ''

    def database_teardown():
        os.remove(TEST_DATABASE_PATH)

    request.addfinalizer(database_teardown)
    return citnet


def test_getby_bibcode(citnet):
    node = citnet.getby_bibcode('1971Sci...174..142S')
    assert node.year == '1971'
    assert node.title == "Cyclic Adenosine 3',5'-Monophosphate during Glucose Repression in the Rat Liver"


def test_write_node(citnet):
    node_in = citnet.getby_bibcode('1971Sci...174..142S')
    db = citnet.db
    assert db.write_node(node_in)
    assert not db.write_node(node_in)
    node_out = db.get_node('1971Sci...174..142S')


def test_get_node(citnet):
    node_in = citnet.getby_bibcode('1971Sci...174..142S')
    db = citnet.db
    db.write_node(node_in)
    node_out = db.get_node('1971Sci...174..142S')
    assert node_in.bibcode == node_out.bibcode
    assert float(node_in.year) == node_out.start



