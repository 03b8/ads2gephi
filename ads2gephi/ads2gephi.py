import os
import ads
from typing import List, Tuple, Iterable
from difflib import SequenceMatcher
from igraph import Graph
from configparser import ConfigParser
from sqlalchemy import Table, Column, Integer, String, Float, Boolean, MetaData, create_engine
from sqlalchemy.sql import select
from tqdm import tqdm

# Load API token from configuration file (or env variable for testing)
home_dir = os.path.expanduser('~')
conf_dir_path = os.path.join(home_dir, '.ads2gephi')
conf_file_path = os.path.join(conf_dir_path, 'ads2gephi.cfg')
if os.path.isfile(conf_file_path):
    config = ConfigParser()
    config.read_file(open(conf_file_path))
    ADS_API_KEY = config['ads_api']['APIKey']
else:
    ADS_API_KEY = os.environ.get('ADS_API_KEY')


class Node:
    """
    A node representing a single publication in the citation network
    """

    def __init__(self, bibcode: str = None, db_article: ads.search.Article = None, judgement: bool = False):
        """
        Create new publication node
        :param bibcode: A bibcode to be queried from ADS
        :param db_article: An Article object to be used instead of querying the ADS
        """
        if db_article:
            self._article = db_article
        elif bibcode:
            _query = ads.SearchQuery(
                bibcode=bibcode,
                token=ADS_API_KEY,
                fl=['bibcode', 'year', 'author', 'title', 'reference', 'citation']
            )
            self._article = _query.next()
            self._modularity_id: int = 0
        self.judgement = judgement

    @property
    def modularity_id(self) -> int:
        return self._modularity_id

    @modularity_id.setter
    def modularity_id(self, mod_id: int) -> None:
        self._modularity_id = mod_id

    @property
    def bibcode(self) -> str:
        return self._article.bibcode

    @property
    def year(self) -> str:
        return self._article.year

    @property
    def author_list(self) -> List[str]:
        return self._article.author

    @property
    def authors(self) -> str:
        author_list = self._article.author
        return '; '.join(author_list)

    @property
    def title(self) -> str:
        title_list = self._article.title
        return '; '.join(title_list)

    @property
    def reference_nodes(self) -> Iterable:
        if self._article.reference:
            for bibcode in self._article.reference:
                yield Node(bibcode=bibcode)
        return []

    @property
    def reference_bibcodes(self) -> Iterable:
        return self._article.reference if self._article.reference else []

    @property
    def citation_nodes(self) -> Iterable:
        if self._article.citation:
            for bibcode in self._article.citation:
                yield Node(bibcode=bibcode)
        return []

    @property
    def citation_bibcodes(self) -> Iterable:
        return self._article.citation if self._article.citation else []


class CitationNetwork:
    """
    A citation network composed of nodes and edges
    """

    def __init__(self):
        self._nodes: List['Node'] = []
        self._edges: List[Tuple] = []

    def __len__(self):
        return len(self.nodes)

    @property
    def nodes(self) -> List['Node']:
        """
        Get the list of nodes in the network
        """
        return self._nodes

    @property
    def edges(self) -> List[Tuple[str, str, int]]:
        """
        Get the list of nodes in the network
        :return: A list of tuples, each representing one edge
                 as (bibcode, bibcode, weight)
        """
        return self._edges

    @edges.setter
    def edges(self, edges: List[Tuple[str, str, int]]) -> None:
        """
        Set the list of edges in the network
        :param edges: A list of edges
        """
        self._edges = edges

    def add_node(self, bibcode: str = None, db_node: Node = None, judgement: bool = False) -> None:
        """
        Add a node to the citation network using its bibcode
        :param bibcode: A bibcode to be queried from ADS
        :param db_node: An already built node from the database
        """
        bibcode = bibcode if bibcode else db_node.bibcode
        if self.has_node(bibcode):
            return
        if bibcode:
            self._nodes.append(Node(bibcode, judgement=judgement))
        elif db_node:
            self._nodes.append(db_node)

    def add_edge(self, edge: Tuple[str, str, int]) -> None:
        """
        Add an edge to the citation network.
        :param edge: Edge as tuple (bibcode, bibcode, weight)
        """
        if self.has_edge(edge):
            return
        self._edges.append(edge)

    def has_node(self, bibcode: str) -> bool:
        """
        Check if a node exists in the network by using its bibcode
        :param bibcode:
        """
        for node in self._nodes:
            if bibcode == node.bibcode:
                return True
        return False

    def node_is_judgement(self, bibcode: str) -> bool:
        """
        Check if a node was added via judgement sampling
        :param bibcode:
        """
        for node in self._nodes:
            if bibcode == node.bibcode:
                return node.judgement
        return ValueError(f"There is no node with bibcode {bibcode} in the sampled network.")

    def has_edge(self, edge: Tuple[str, str, int]) -> bool:
        """
        Check if an edge exists in the network.
        The edge is a tuple containing (source_bibcode, target_bibcode, weight)
        :param edge: Edge as tuple (bibcode, bibcode, weight)
        """
        for old_edge in self._edges:
            if old_edge == edge:
                return True
        return False

    def sample_judgement(self, bibcodes: Iterable[str]) -> None:
        """
        Sample a list of bibcodes
        :param bibcodes:
        """
        for bibcode in bibcodes:
            self.add_node(bibcode, judgement=True)

    def sample_snowball(self, year_interval: Tuple[str, str], scope: str) -> None:
        """
        Sample citation and/or reference nodes from existing nodes
        :param year_interval:
        :param scope:
        """
        sampled_nodes = []
        start_year = year_interval[0]
        end_year = year_interval[1]
        for node in self.nodes:
            if 'cit' in scope:
                sampled_nodes += [
                    cit_bibcode for cit_bibcode in node.citation_bibcodes
                    if start_year <= cit_bibcode[:4] <= end_year and
                    not self.has_node(cit_bibcode)
                ]
            if 'ref' in scope:
                sampled_nodes += [
                    ref_bibcode for ref_bibcode in node.reference_bibcodes
                    if start_year <= ref_bibcode[:4] <= end_year and
                    not self.has_node(ref_bibcode)
                ]

        nodes = tqdm(sampled_nodes)
        for bibcode in nodes:
            nodes.set_description(f'Processing {bibcode}')
            self.add_node(bibcode)

    @staticmethod
    def author_is_same(name_1: str, name_2: str) -> bool:
        """
        Assess if two author names are similar enough to refer to the same person
        by doing a fuzzy string comparison using the Ratcliff/Obershelp algorithm.
        TODO: Improve precision, check more edge cases
        :param name_1
        :param name_2
        """
        name1_last, name1_first = tuple(name_1.split(', '))
        name2_last, name2_first = tuple(name_2.split(', '))
        name1_initial = name1_first[0]
        name2_initial = name2_first[0]
        if name1_initial != name2_initial:
            return False
        score = (
             SequenceMatcher(None, name1_initial, name2_initial).ratio() +
             SequenceMatcher(None, name1_last, name2_last).ratio() * 9
        ) / 10.0
        if score > 0.80:
            return True
        return False

    def make_regular_edges(self) -> None:
        """
        Generate edges pointing from citing to cited node
        """
        for node in self._nodes:
            adjacent_nodes_cit = [
                (adjacent_node_bibcode, node.bibcode, 0)
                for adjacent_node_bibcode in node.citation_bibcodes
                if self.has_node(adjacent_node_bibcode)
            ]
            adjacent_nodes_ref = [
                (node.bibcode, adjacent_node_bibcode, 0)
                for adjacent_node_bibcode in node.reference_bibcodes
                if self.has_node(adjacent_node_bibcode)
            ]
            any(
                self.add_edge(edge)
                for edge in [*adjacent_nodes_cit, *adjacent_nodes_ref]
            )

    def make_semsim_edges(self, measure) -> None:
        """
        Generate edges pointing from citing to cited node
        :param measure: Semantic similarity measure: 'cocit' for co-citation
        or bibliographic coupling ('bibcp')
        """
        self.make_regular_edges()
        graph = Graph(directed=True)
        vertices = [node.bibcode for node in self.nodes]
        graph.add_vertices(vertices)
        regular_edges = [
            (edge[0], edge[1])
            for edge in self.edges
        ]
        graph.add_edges(regular_edges)
        if measure == 'cocit':
            matrix = graph.cocitation()
        elif measure == 'bibcp':
            matrix = graph.bibcoupling()
        else:
            raise ValueError('Measure type not valid.')
        semsim_edges = [
            (
                 vertices[source_vertex_index],
                 vertices[target_vertex_index],
                 weight
            )
            for source_vertex_index, target_vertices in enumerate(matrix)
            for target_vertex_index, weight in enumerate(
                target_vertices[:source_vertex_index]
            )
            if source_vertex_index != target_vertex_index and weight > 0
        ]
        self._edges = semsim_edges

    def assign_modularity(self) -> None:
        """
        Assign modularity to nodes using the community infomap algorithm
        """
        graph = Graph(directed=True)
        vertices = [node.bibcode for node in self.nodes]
        graph.add_vertices(vertices)
        edges = [
            (edge[0], edge[1])
            for edge in self.edges
        ]
        graph.add_edges(edges)
        modularity = {
            vertices[node_index]: module_id
            for module_id, module in enumerate(
                graph.community_infomap(trials=1)
            )
            for node_index in module
        }
        for node in self._nodes:
            node.modularity_id = modularity[node.bibcode]


class Database:
    """
    SQLite database modelled for a citation network
    """

    def __init__(self, path):
        """
        Initialize a SQLite database for a citation network
        :param path: Path where database will be saved
        """
        self._engine = create_engine(f'sqlite:///{path}')
        self._conn = self._engine.connect()
        self._metadata = MetaData()
        self._nodes = Table(
            'nodes',
            self._metadata,
            Column('id', Integer, primary_key=True),
            Column('bibcode', String(20)),
            Column('author', String(255)),
            Column('title', String(255)),
            Column('start', Float),
            Column('end', Float),
            Column('citation', String(3000)),
            Column('reference', String(3000)),
            Column('ordervar', Float),
            Column('cluster_id', Integer),
            Column('judgement', String(8))
        )
        self._edges = Table(
            'edges',
            self._metadata,
            Column('id', Integer, primary_key=True),
            Column('source', Integer),
            Column('target', Integer),
            Column('weight', Integer)
        )
        self._metadata.create_all(self._engine)
        self.citnet = CitationNetwork()

    def node_in_db(self, bibcode: str) -> bool:
        """
        Check by bibcode if node already exists in db
        :param bibcode:
        """
        db_nodes = self._conn.execute(
            select([self._nodes])
        )
        for node in db_nodes:
            if bibcode == node.bibcode:
                return True
        return False

    def edge_in_db(self, edge: Tuple[str, str, int]) -> bool:
        """
        Check by bibcode if node already exists in db
        :param edge: Edge as tuple (bibcode, bibcode, weight)
        """
        db_edges = self._conn.execute(
            select([self._edges])
        )
        for db_edge in db_edges:
            if db_edge[1:3] == edge[:2]:
                return True
        return False

    def write_citnet_to_db(self) -> None:
        """
        Map and save citation network from CitationNetwork object to db
        """
        for node in self.citnet.nodes:
            if not self.node_in_db(node.bibcode):
                insertion = self._nodes.insert().values(
                    bibcode=node.bibcode,
                    author=node.authors,
                    title=node.title,
                    start=node.year, end=node.year,
                    ordervar=(int(node.year) - 1900) / 100,
                    citation='; '.join(node.citation_bibcodes),
                    reference='; '.join(node.reference_bibcodes),
                    cluster_id=node.modularity_id,
                    judgement=str(node.judgement)
                )
                self._conn.execute(insertion)
        for edge in self.citnet.edges:
            # This filters out edges whose source node doesn't belong to the judgement sample
            # TODO: Consider making this an option to be toggled from the CLI
            if not self.edge_in_db(edge) and self.citnet.node_is_judgement(edge[0]):
                insertion = self._edges.insert().values(
                    source=edge[0],
                    target=edge[1],
                    weight=edge[2]
                )
                self._conn.execute(insertion)

    def read_citnet_from_db(self) -> None:
        """
        Map and load citation network from db to CitationNetwork object
        """
        db_nodes = self._conn.execute(
            select([self._nodes])
        )
        db_edges = self._conn.execute(
            select([self._edges])
        )
        citnet_nodes = []
        for db_node in db_nodes:
            db_article = ads.search.Article(  # Is this necessary? Shouldn't db be imported w/o API calls?
                bibcode=db_node.bibcode,
                title=[db_node.title],
                year=db_node.start,
                author=db_node.author.split('; '),
                citation=db_node.citation.split('; '),
                reference=db_node.reference.split('; ')
            )
            citnet_node = Node(db_article=db_article)
            citnet_node.modularity_id = db_node.cluster_id
            citnet_nodes.append(citnet_node)
            self.citnet.add_node(db_node=citnet_node)
        for db_edge in db_edges:
            self.citnet.add_edge(
                (db_edge.source, db_edge.target, db_edge.weight)
            )

