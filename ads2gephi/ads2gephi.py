import ads
import igraph
from configparser import ConfigParser
from sqlalchemy import Table, Column, Integer, String, Float, MetaData, create_engine, text
from sqlalchemy.sql import select, and_
from ads.exceptions import APIResponseError
from difflib import SequenceMatcher


class CitationNetwork(object):
    def __init__(self, filename):
        self.db = Database(filename)
        self.nodelist = self.db.get_all_nodes()
        self.edgelist = self.db.get_all_edges()
        # List of bibcodes for judgement sampling
        self.bibcode_list = []
        # Year interval for snowball sampling
        self.snowball = {'start': '', 'end': '', 'scope': ''}

    def parse_config(self, config_file):
        """
        Parse the configuration file and set object parameters according to the parsed values.
        :param config_file: path to configuration file
        :return: None
        """
        # Read configuration file
        config = ConfigParser()
        config.read_file(open(config_file))
        # Assign API Key from configuration file
        ads.config.token = config['ads_api']['APIKey']
        # Assign default interval years for snowball sampling from configuration file
        self.snowball['start'] = int(config['snowball_default_interval']['StartYear'])
        self.snowball['end'] = int(config['snowball_default_interval']['EndYear'])

    def sample(self, sampling_method):
        """
        Initialize node sampling and write sample to database.
        :param sampling_method: 'snowball' or 'judgement'
        :return: None
        """

        if sampling_method == 'snowball':
            queried_nodes = self.smp_snowball(self.nodelist,
                                              self.snowball['start'],
                                              self.snowball['end'],
                                              self.snowball['scope'])
        elif sampling_method == 'judgement':
            queried_nodes = [self.getby_bibcode(bc) for bc in self.bibcode_list]
        else:
            raise ValueError('Parameter sampling_method is invalid')

        print('Writing nodes to database file...')
        self.db.write_nodes(queried_nodes)
        print('Finished writing nodes.')

    @staticmethod
    def author_is_same(node1, node2):
        """
        Check if first author is the same in two nodes by doing a fuzzy
        string comparison using the Ratcliff/Obershelp algorithm.
        :return: boolean
        """
        # Get name of first authors
        name1 = node1.author.split('; ')[0]
        name2 = node2.author.split('; ')[0]

        # Split in first and last name
        name1_split = name1.split(', ')
        name2_split = name2.split(', ')

        try:
            name1_init = name1_split[1].split(' ')[0][0]
        except IndexError:
            name1_init = ''

        try:
            name2_init = name2_split[1].split(' ')[0][0]
        except IndexError:
            name2_init = ''

        score = (SequenceMatcher(None, name1_init, name2_init).ratio() +
                 SequenceMatcher(None, name1_split[0], name2_split[0]).ratio()) / 2.0

        if score > 0.80:
            return True
        else:
            return False

    @staticmethod
    def getby_bibcode(bibcode):
        """
        Query an ADS item by bibcode.
        :param bibcode: bibcode (ADS unique identifier)
        :return: queried item as Node object
        """
        for i in range(5):
            try:
                query = ads.SearchQuery(bibcode=bibcode,
                                        fl=['author', 'year', 'title',
                                            'bibcode', 'reference', 'citation'])

                for item in query:
                    new_node = Node(item)
                    if new_node is not None:
                        return new_node
                    else:
                        print('Couldn\'t make node for bibcode {}'.format(bibcode))
            except (IndexError, APIResponseError):
                print('Error occured while querying ADS. Retrying...')
                continue

    @staticmethod
    def smp_snowball(nodelist, start_year, end_year, scope):
        """
        Extend existing network by sampling through its citation and/or reference columns
        and selecting new items if they fit into the given time frame.
        :param nodelist: list of nodes from local database
        :param start_year: starting year of time frame as integer
        :param end_year: end year of time frame as integer
        :param scope: 'cit' (only citation), 'ref' (only reference), 'citref' (both citation and reference)
        :return: list of selected items as Node objects
        """

        node_accumulator = []

        if scope == 'cit':
            print('Initializing sampler...')
            for node in nodelist:
                if node.citation is not None:
                    for bc in node.citation.split('; '):
                        print('Checking bibcode {}'.format(bc))
                        if start_year < int(bc[0:4]) < end_year:
                            print('Querying ADS...')
                            for i in range(5):
                                try:
                                    query = ads.SearchQuery(bibcode=bc,
                                                            fl=['author', 'year', 'title',
                                                                'bibcode', 'reference', 'citation'])
                                    for item in query:
                                        node_accumulator.append(Node(item))
                                        print('Node added to accumulator.')
                                    break
                                except (IndexError, APIResponseError):
                                    print('Error occured while querying ADS. Retrying...')
                                    continue
                        else:
                            print('Bibcode not in year interval. Skipping...')

        elif scope == 'ref':
            print('Initializing sampler...')
            for node in nodelist:
                if node.reference is not None:
                    for bc in node.reference.split('; '):
                        print('Checking bibcode {}'.format(bc))
                        if start_year < int(bc[0:4]) < end_year:
                            print('Querying ADS...')
                            for i in range(5):
                                try:
                                    query = ads.SearchQuery(bibcode=bc,
                                                            fl=['author', 'year', 'title',
                                                                'bibcode', 'reference', 'citation'])
                                    for item in query:
                                        node_accumulator.append(Node(item))
                                        print('Node added to accumulator.')
                                    break
                                except (IndexError, APIResponseError):
                                    print('Error occured while querying ADS. Retrying...')
                                    continue
                        else:
                            print('Bibcode not in year interval. Skipping...')

        elif scope == 'citref':
            print('Initializing sampler...')
            for node in nodelist:
                if node.citation is not None:
                    for bc in node.citation.split('; '):
                        print('Checking bibcode {}'.format(bc))
                        if start_year < int(bc[0:4]) < end_year:
                            print('Querying ADS...')
                            for i in range(5):
                                try:
                                    query = ads.SearchQuery(bibcode=bc,
                                                            fl=['author', 'year', 'title',
                                                                'bibcode', 'reference', 'citation'])
                                    for item in query:
                                        node_accumulator.append(Node(item))
                                        print('Node added to accumulator.')
                                    break
                                except (IndexError, APIResponseError):
                                    print('Error occured while querying ADS. Retrying...')
                                    continue
                        else:
                            print('Bibcode not in year interval. Skipping...')

                if node.reference is not None:
                    for bc in node.reference.split('; '):
                        print('Checking bibcode {}'.format(bc))
                        if start_year < int(bc[0:4]) < end_year:
                            print('Querying ADS...')
                            for i in range(5):
                                try:
                                    query = ads.SearchQuery(bibcode=bc,
                                                            fl=['author', 'year', 'title',
                                                                'bibcode', 'reference', 'citation'])
                                    for item in query:
                                        node_accumulator.append(Node(item))
                                    break
                                except (IndexError, APIResponseError):
                                    continue
                        else:
                            print('Bibcode not in year interval. Skipping...')

        print('Returning accumulator with {} items...'.format(len(node_accumulator)))
        return node_accumulator

    def make_regular_edges(self, direction):
        """
        Generate regular, directed edges, either forwards (from cited to citing note)
        or backwards (from citing to cited node) and write edges to database.
        :param direction: fwd (forwards), bwd (backwards);
        :return: None
        """

        for node in self.nodelist:

            if node.citation is not None:
                for citation_bc in node.citation.split('; '):
                    if self.db.get_node(citation_bc) is not None:
                        if not self.author_is_same(self.db.get_node(citation_bc), node):
                            citation_id = self.db.get_node(citation_bc).id
                            if direction == 'fwd':
                                self.db.write_edge((node.id, citation_id, None))
                            elif direction == 'bwd':
                                self.db.write_edge((citation_id, node.id, None))
                            else:
                                raise ValueError("Direction type not valid.")

            if node.reference is not None:
                for reference_bc in node.reference.split('; '):
                    if self.db.get_node(reference_bc) is not None:
                        if not self.author_is_same(self.db.get_node(reference_bc), node):
                            reference_id = self.db.get_node(reference_bc).id
                            if direction == 'fwd':
                                self.db.write_edge((reference_id, node.id, None))
                            elif direction == 'bwd':
                                self.db.write_edge((node.id, reference_id, None))
                            else:
                                raise ValueError("Direction type not valid.")

    def make_semsim_edges(self, measure):
        """
        Generate edges by semantic similarity (co-citation or bibliographic coupling) and write them to databse.
        :param measure: 'cocit' (co-citation) or 'bibcp' (bibliographic coupling)
        :return: None
        """

        g = igraph.Graph(directed=True)
        g.add_vertices(len(self.nodelist) + 1)
        self.db.del_table_content('edges')
        self.make_regular_edges('bwd')
        edges = self.db.get_all_edges()
        g.add_edges([(edge[1], edge[2]) for edge in edges])
        new_edges = []

        if measure == 'cocit':
            matrix = g.cocitation()
        elif measure == 'bibcp':
            matrix = g.bibcoupling()
        else:
            raise ValueError("Measure type not valid.")

        for i1, v1 in enumerate(matrix):
            for i2, v2 in enumerate(matrix):
                if matrix[i1][i2] > 0:
                    index = matrix[i1][i2]
                    if (i1, i2, index) not in new_edges:
                        new_edges.append((i1, i2, index))

        self.db.del_table_content('edges')
        self.db.write_edges(new_edges)

    def assign_modularity(self):
        g = igraph.Graph(directed=True)
        g.add_vertices(len(self.nodelist) + 1)
        edges = self.db.get_all_edges()
        g.add_edges([(edge[1], edge[2]) for edge in edges])
        modularity = [i for i in g.community_infomap(trials=1)]
        for node in self.nodelist:
            for cluster_id in modularity:
                for node_id in cluster_id:
                    if node.id == node_id:
                        self.db.set_node_cluster(int(node_id), int(modularity.index(cluster_id)))


class Node(object):
    # TODO: Write docstrings
    def __init__(self, ads_obj):
        self.bibcode = ads_obj.bibcode
        try:
            self.author = "; ".join(ads_obj.author)
        except TypeError:
            self.author = str(ads_obj.author)
        if ads_obj.title is not None:
            self.title = "; ".join(ads_obj.title)
        else:
            self.title = None
        self.year = ads_obj.year
        self.citation = ads_obj.citation
        self.reference = ads_obj.reference
        self.cluster_id = None

    def get_bibcode(self):
        return self.bibcode

    def get_author(self):
        return self.author

    def get_title(self):
        return self.title

    def get_year(self):
        return self.year

    def get_citation(self):
        return self.citation

    def get_reference(self):
        return self.reference

    def get_cluster_id(self):
        return self.cluster_id

    def __repr__(self):
        return "Node(bibcode={}, author={}, title={}, year={}" \
            .format(self.bibcode, self.author, self.title, self.year)


class Database(object):
    # TODO: Write docstrings
    def __init__(self, filename):
        self.engine = create_engine('sqlite:///{}'.format(filename))
        self.conn = self.engine.connect()
        self.metadata = MetaData()

        self.nodes = Table('nodes', self.metadata,
                           Column('id', Integer, primary_key=True), Column('bibcode', String(20)),
                           Column('author', String(255)), Column('title', String(255)),
                           Column('start', Float), Column('end', Float), Column('citation', String(3000)),
                           Column('reference', String(3000)), Column('type', String(2)),
                           Column('ordervar', Float), Column('cluster_id', Integer),
                           Column('cluster_id', Integer))

        self.edges = Table('edges', self.metadata,
                           Column('id', Integer, primary_key=True),
                           Column('source', Integer),
                           Column('target', Integer),
                           Column('weight', Integer))

        self.metadata.create_all(self.engine)

    def get_all_nodes(self):
        return [node for node in self.conn.execute(select([self.nodes]))]

    def get_all_edges(self):
        return [edge for edge in self.conn.execute(select([self.edges]))]

    def get_node(self, bibcode):
        node_query = self.conn.execute(select([self.nodes]).where(self.nodes.c.bibcode == bibcode))
        return node_query.fetchone()

    def set_node_cluster(self, node_id, value):
        stmt = self.nodes.update().where(self.nodes.c.id == node_id).values(cluster_id=value)
        self.conn.execute(stmt)

    def is_in_db(self, item_type, item):
        """
        Check if a specific item is already in the database. Search for nodes by bibcode.
        :param item_type: node, edge or bibcode
        :param item: if node, Node object; if edge, tuple
        :return: boolean
        """
        assert item_type in ['node', 'edge', 'bibcode']
        if item_type == 'node':
            node_query = self.conn.execute(select([self.nodes]).where(self.nodes.c.bibcode == item.bibcode))
            return node_query.fetchone() is not None
        elif item_type == 'edge':
            edge_query = self.conn.execute(select([self.edges]).where(and_(self.edges.c.source == item[0],
                                                                           self.edges.c.target == item[1])))
            return edge_query.fetchone() is not None
        elif item_type == 'bibcode':
            node_query = self.conn.execute(select([self.nodes]).where(self.nodes.c.bibcode == item))
            return node_query.fetchone() is not None

    def del_table_content(self, table_name):
        if table_name == 'nodes':
            self.conn.execute(text('DELETE FROM nodes'))
        elif table_name == 'edges':
            self.conn.execute(text('DELETE FROM edges'))
        else:
            raise ValueError("Parameter table_name not valid.")

    def write_nodes(self, node_list):
        assert type(node_list) is list, 'Parameter node_list is not a list.'

        for node in node_list:
            if type(node) == Node:
                if not self.is_in_db('node', node):
                    bibcode = node.get_bibcode()
                    author = node.get_author()
                    title = node.get_title()
                    year = node.get_year()
                    if node.get_citation() is not None:
                        citation = '; '.join(node.get_citation())
                    else:
                        citation = None
                    if node.get_reference() is not None:
                        reference = '; '.join(node.get_reference())
                    else:
                        reference = None
                    cluster_id = node.get_cluster_id()

                    insertion = self.nodes.insert().values(bibcode=bibcode,
                                                           author=author,
                                                           title=title,
                                                           start=year, end=year,
                                                           ordervar=(int(year) - 1900) / 100,
                                                           citation=citation,
                                                           reference=reference,
                                                           cluster_id=cluster_id)
                    self.conn.execute(insertion)
                else:
                    print("Item with bibcode '{}' already in database!".format(node.get_bibcode()))
            else:
                pass

    def write_node(self, node):
        if not self.is_in_db('node', node):
            bibcode = node.get_bibcode()
            author = node.get_author()
            title = node.get_title()
            year = node.get_year()
            if node.get_citation() is not None:
                citation = '; '.join(node.get_citation())
            else:
                citation = None
            if node.get_reference() is not None:
                reference = '; '.join(node.get_reference())
            else:
                reference = None
            cluster_id = node.get_cluster_id()

            insertion = self.nodes.insert().values(bibcode=bibcode,
                                                   author=author,
                                                   title=title,
                                                   start=year, end=year,
                                                   ordervar=(int(year) - 1900) / 100,
                                                   citation=citation,
                                                   reference=reference,
                                                   cluster_id=cluster_id)
            self.conn.execute(insertion)
            print("Item with bibcode '{}' added to database!".format(node.get_bibcode()))
            return True
        else:
            print("Item with bibcode '{}' already in database!".format(node.get_bibcode()))
            return False

    def write_edges(self, edgelist):
        assert type(edgelist) is list, 'Parameter edgelist is not a list.'

        for edge in edgelist:
            if not self.is_in_db('edge', edge):
                insertion = self.edges.insert().values(source=edge[0], target=edge[1], weight=edge[2])
                self.conn.execute(insertion)

    def write_edge(self, edge):
        assert type(edge) is tuple, 'Parameter edge is not a tuple'

        if not self.is_in_db('edge', edge):
            insertion = self.edges.insert().values(source=edge[0], target=edge[1], weight=edge[2])
            self.conn.execute(insertion)
