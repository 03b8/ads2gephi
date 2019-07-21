# ads2gephi

is a command line tool for querying and modeling citation networks from the Astrophysical Data System (ADS) in a format compatible with Gephi, a popular network visualization tool. ads2gephi has been developed at the history of science department of TU Berlin as part of a research project on the history of extragalactic astronomy.

### Usage

When using the tool for the first time to model a network, you will be prompted to enter your ADS API key. Your key will then be stored in a configuration file under ~/.ads2gephi.

In order to sample an initial citation network, you need to provide ads2gephi with a plain text file with bibcodes (ADS unique identifiers), one per line, as input. The queried network will be output in a SQLite database stored in the current directory:

```
ads2gephi -c bibcodes_example.txt -d my_fancy_netzwerk.db
```

Afterwards you can extend the queried network by providing the existing database file and using the additional sampling options. For example, you can extend the network by querying all the items cited in every publication previously queried:

```
ads2gephi -s ref -d network_database_example.db 
```

Finally you might want to also generate the edges of the network. There are several options for generating edges. For example you can use a semantic similarity measure like bibliographic coupling or co-citation:
```
ads2gephi -e bibcp -d network_database_example.db
```

All other querying and modelling options are described in the help page:
```
ads2gephi -h
```

Once you're finished querying and modeling, fhe database file can be directly imported in Gephi for network visualization and analysis.

## Special thanks to

* Edwin Henneken
