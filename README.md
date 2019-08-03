[![PyPI version](https://badge.fury.io/py/ads2gephi.svg)](https://badge.fury.io/py/ads2gephi)
![build](https://api.travis-ci.org/03b8/ads2gephi.svg?branch=master)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# ads2gephi

is a command line tool for querying and modeling citation networks from the Astrophysical Data System (ADS) in a format compatible with Gephi, a popular network visualization tool. ads2gephi has been developed at the history of science department of TU Berlin as part of a research project on the history of extragalactic astronomy.

You can install `ads2gephi` from PyPI:
```
pip install ads2gephi
```

### Usage

When using the tool for the first time to model a network, you will be prompted to enter your ADS API key. Your key will then be stored in a configuration file under ~/.ads2gephi.

In order to sample an initial citation network, you need to provide ads2gephi with a plain text file with bibcodes (ADS unique identifiers), one per line, as input. The queried network will be output in a SQLite database stored in the current directory:

```
ads2gephi -c bibcodes_example.txt -d my_fancy_netzwerk.db
```

Afterwards you can extend the queried network by providing the existing database file and using the additional sampling options. For example, you can extend the network by querying all the items cited in every publication previously queried:

```
ads2gephi -s ref -d my_fancy_netzwerk.db
```

Finally you might want to also generate the edges of the network. There are several options for generating edges. For example you can use a semantic similarity measure like bibliographic coupling or co-citation:
```
ads2gephi -e bibcp -d my_fancy_netzwerk.db
```

You can also do everything at once:
```
ads2gephi -c bibcodes_example.txt -s ref -e bibcp -d my_fancy_netzwerk.db
```

All other querying and modelling options are described in the help page:
```
ads2gephi --help
```

Once you've finished querying and modeling, the database file can be directly imported in Gephi for network visualization and analysis.

## Special thanks to

* Edwin Henneken
