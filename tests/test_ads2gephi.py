import os
import pytest
from ads2gephi.ads2gephi import Node, CitationNetwork, Database

TEST_NODE = {
    'bibcode': '1968IAUS...29...11A',
    'year': '1968',
    'title': 'On the activity of galactic nuclei (introductory lecture)',
    'authors': 'Ambartsumian, V. A.',
    'citation_bibcodes': [
        '2012ASSL..386...11D', '2010Ap.....53...42H',
        '2008Ap.....51..313B', '1975NW.....62..309F'
    ],
    'reference_bibcodes': ['1963RvMP...35..947B']
}


@pytest.fixture()
def citnet():
    """
    Check if nodes added by judgement sampling are correct
    """
    citnet = CitationNetwork()
    citnet.sample_judgement(bibcodes=[TEST_NODE['bibcode']])
    return citnet


def test_database_init():
    """
    Check if database file is created then initiating db object
    """
    db_path = 'tests/ads2gephi_test.db'
    Database(db_path)
    assert os.path.exists('tests/ads2gephi_test.db')
    os.remove(db_path)


def test_database_readwrite_citnet():
    """
    Check if Database loads and writes CitationNetwork
    """
    db_path = 'tests/ads2gephi_test.db'
    citnet = CitationNetwork()
    db = Database(db_path)
    db.write_citnet_to_db()
    db.read_citnet_from_db()
    assert len(db.citnet) == len(citnet)
    os.remove(db_path)


def test_citnet_sample_judgement(citnet):
    """
    Check if nodes added by judgement sampling are correct
    """
    sampled_bibcodes = {node.bibcode for node in citnet.nodes}
    expected_bibcodes = {TEST_NODE['bibcode']}
    assert expected_bibcodes == sampled_bibcodes


def test_citnet_sample_snowball_cit(citnet):
    """
    Check if nodes added by snowball sampling from citation are correct
    """
    citnet.sample_snowball(scope='cit', year_interval=('1975', '2012'))
    sampled_bibcodes = {node.bibcode for node in citnet.nodes}
    expected_bibcodes = {
        TEST_NODE['bibcode'],
        *TEST_NODE['citation_bibcodes']
    }
    assert sampled_bibcodes == expected_bibcodes


def test_citnet_sample_snowball_ref(citnet):
    """
    Check if nodes added by snowball sampling from reference are correct
    """
    citnet.sample_snowball(scope='ref', year_interval=('1963', '2012'))
    sampled_bibcodes = {node.bibcode for node in citnet.nodes}
    expected_bibcodes = {
        TEST_NODE['bibcode'],
        *TEST_NODE['reference_bibcodes']
    }
    assert sampled_bibcodes == expected_bibcodes


def test_citnet_sample_snowball_citref(citnet):
    """
    Check if nodes added by snowball sampling from both citation
    and reference are correct
    """
    citnet.sample_snowball(scope='cit+ref', year_interval=('1963', '2012'))
    sampled_bibcodes = {node.bibcode for node in citnet.nodes}
    expected_bibcodes = {
        TEST_NODE['bibcode'],
        *TEST_NODE['citation_bibcodes'], *TEST_NODE['reference_bibcodes']
    }
    assert sampled_bibcodes == expected_bibcodes


def test_citnet_sample_snowball_citref_years(citnet):
    """
    Check if nodes added by snowball sampling from both citation
    and reference are correct with a year interval restraint
    """
    citnet.sample_snowball(scope='cit+ref', year_interval=('1963', '1975'))
    sampled_bibcodes = {node.bibcode for node in citnet.nodes}
    expected_bibcodes = {
        TEST_NODE['bibcode'],
        '1963RvMP...35..947B', '1975NW.....62..309F'
    }
    assert sampled_bibcodes == expected_bibcodes


def test_citnet_make_regular_edges(citnet):
    """
    Check if generated regular edges are correct
    """
    citnet.sample_snowball(scope='cit+ref', year_interval=('1963', '2012'))
    citnet.make_regular_edges(remove_selfcitations=False)
    generated_edges = set(citnet.edges)
    expected_edges = {
        ('2012ASSL..386...11D', '1968IAUS...29...11A', 0),
        ('2010Ap.....53...42H', '1968IAUS...29...11A', 0),
        ('2008Ap.....51..313B', '1968IAUS...29...11A', 0),
        ('1975NW.....62..309F', '1968IAUS...29...11A', 0),
        ('1968IAUS...29...11A', '1963RvMP...35..947B', 0),
        ('2012ASSL..386...11D', '1963RvMP...35..947B', 0),
    }
    assert generated_edges == expected_edges


def test_citnet_make_semsim_edges_bibcp(citnet):
    """
    Check if generated bibliographical coupling edges are correct
    """
    citnet.sample_snowball(scope='cit+ref', year_interval=('1962', '2012'))
    citnet.make_semsim_edges('bibcp')
    generated_edges = set(citnet.edges)
    expected_edges = {
        ('2012ASSL..386...11D', '2010Ap.....53...42H', 1),
        ('2012ASSL..386...11D', '2008Ap.....51..313B', 1),
        ('2012ASSL..386...11D', '1975NW.....62..309F', 1),
        ('2012ASSL..386...11D', '1968IAUS...29...11A', 1),
        ('2010Ap.....53...42H', '2008Ap.....51..313B', 1),
        ('2010Ap.....53...42H', '1975NW.....62..309F', 1),
        ('2008Ap.....51..313B', '1975NW.....62..309F', 1),
    }
    assert generated_edges == expected_edges


def test_citnet_make_semsim_edges_cocit(citnet):
    """
    Check if generated cocitation edges are correct
    """
    citnet.sample_snowball(scope='cit+ref', year_interval=('1962', '2012'))
    citnet.make_semsim_edges('cocit')
    generated_edges = set(citnet.edges)
    expected_edges = {
        ('1963RvMP...35..947B', '1968IAUS...29...11A', 1),
    }
    assert generated_edges == expected_edges


def test_citnet_assign_modularity_regular_edges(citnet):
    """
    Check if assigned modularity IDs are correct
    """
    citnet.sample_snowball(scope='cit+ref', year_interval=('1962', '2012'))
    citnet.make_regular_edges(remove_selfcitations=False)
    citnet.assign_modularity()
    generated_values = {
        (node.bibcode, node.modularity_id)
        for node in citnet.nodes
    }
    expected_values = {
        ('1968IAUS...29...11A', 0),
        ('2012ASSL..386...11D', 0),
        ('2010Ap.....53...42H', 0),
        ('2008Ap.....51..313B', 0),
        ('1975NW.....62..309F', 0),
        ('1963RvMP...35..947B', 0),

    }
    assert generated_values == expected_values


def test_citnet_assign_modularity_cocit_edges(citnet):
    """
    Check if assigned modularity IDs are correct for cocitation edges
    """
    citnet.sample_snowball(scope='cit+ref', year_interval=('1962', '2012'))
    citnet.make_semsim_edges(measure='cocit')
    citnet.assign_modularity()
    generated_values = {
        (node.bibcode, node.modularity_id)
        for node in citnet.nodes
    }
    expected_values = {
        ('1963RvMP...35..947B', 0),
        ('1968IAUS...29...11A', 0),
        ('2012ASSL..386...11D', 1),
        ('2010Ap.....53...42H', 2),
        ('2008Ap.....51..313B', 3),
        ('1975NW.....62..309F', 4),

    }
    assert generated_values == expected_values


def test_citnet_assign_modularity_bibcp_edges(citnet):
    """
    Check if assigned modularity IDs are correct for bibligraphical coupling edges
    """
    citnet.sample_snowball(scope='cit+ref', year_interval=('1962', '2012'))
    citnet.make_semsim_edges(measure='bibcp')
    citnet.assign_modularity()
    generated_values = {
        (node.bibcode, node.modularity_id)
        for node in citnet.nodes
    }
    expected_values = {
        ('2012ASSL..386...11D', 0),
        ('1968IAUS...29...11A', 0),
        ('2010Ap.....53...42H', 0),
        ('2008Ap.....51..313B', 0),
        ('1975NW.....62..309F', 0),
        ('1963RvMP...35..947B', 1),

    }
    assert generated_values == expected_values


def test_citnet_author_identity_different():
    """
    Check functionality of of author identity checker
    """
    citnet = CitationNetwork()
    assert not citnet.author_is_same('Burbidge, X. Y.', 'Burbidge, A. B.')
    assert not citnet.author_is_same('Arp, A.', 'Arp, Hans')
    assert not citnet.author_is_same('Bergmann, Hans Albert', 'Berg, H.')


def test_citnet_author_identity_same():
    """
    Check functionality of of author identity checker
    """
    citnet = CitationNetwork()
    assert citnet.author_is_same('Burbidge, X. Y.', 'Burbidge, Xenya Yakupova')
    assert citnet.author_is_same('Ambartsumyan, V.', 'Ambartsumian, V. A.')
    assert citnet.author_is_same('Ambarcuman, Viktor', 'Ambartsumian, V. A.')


def test_citnet_add_node():
    """
    Check if a node is added correctly
    """
    citnet = CitationNetwork()
    citnet.add_node(TEST_NODE['bibcode'])
    assert citnet.has_node(TEST_NODE['bibcode'])


def test_citnet_add_node_two_times():
    """
    Make sure that no duplicates can be added
    """
    citnet = CitationNetwork()
    citnet.add_node(TEST_NODE['bibcode'])
    citnet.add_node(TEST_NODE['bibcode'])
    assert len(citnet.nodes) == 1


def test_citnet_add_edge():
    """
    Check if an edge is added correctly
    """
    citnet = CitationNetwork()
    edge = ('1975NW.....62..309F', '1963RvMP...35..947B', 0)
    citnet.add_edge(edge)
    assert citnet.has_edge(edge)


def test_citnet_add_edge_two_times():
    """
    Make sure that no duplicates can be added
    """
    citnet = CitationNetwork()
    edge = ('1975NW.....62..309F', '1963RvMP...35..947B', 0)
    citnet.add_edge(edge)
    citnet.add_edge(edge)
    assert len(citnet.edges) == 1


def test_node_static_properties():
    """
    Test properties copied by Node from ads.search.Article
    """
    node = Node(TEST_NODE['bibcode'])
    assert node.bibcode == TEST_NODE['bibcode']
    assert node.year == TEST_NODE['year']


def test_node_dynamic_properties():
    """
    Test properties processed by Node
    """
    node = Node(TEST_NODE['bibcode'])
    assert node.title == TEST_NODE['title']
    assert node.author_list == [TEST_NODE['authors']]
    assert node.authors == TEST_NODE['authors']


def test_node_init_citation():
    """
    Test node generator for citation property
    """
    node = Node(TEST_NODE['bibcode'])
    expected_bibcodes = TEST_NODE['citation_bibcodes']
    citation_bibcodes = [cit_node.bibcode for cit_node in node.citation_nodes]
    assert set(expected_bibcodes) & set(citation_bibcodes)


def test_node_init_reference():
    """
    Test node generator for reference property
    """
    node = Node(TEST_NODE['bibcode'])
    expected_bibcodes = TEST_NODE['reference_bibcodes']
    reference_bibcodes = [cit_node.bibcode for cit_node in node.reference_nodes]
    assert set(expected_bibcodes) & set(reference_bibcodes)
