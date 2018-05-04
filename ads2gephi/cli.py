import os
import argparse
from configparser import ConfigParser
from ads2gephi.ads2gephi import CitationNetwork


def parse_args():
    """
    Creates command line arguments
    :return: Argument parser object
    """

    parser = argparse.ArgumentParser(description='ads2gephi is a command line tool for querying citation networks '
                                                 'from the Astrophysical Data System (ADS) in a format compatible with '
                                                 'Gephi, a popular network visualization tool.')

    parser.add_argument('-v', '--version',
                        help='show version',
                        action='store_true')

    parser.add_argument('-a', '--api-key', help='set and save the ADS API key', type=str)

    parser.add_argument('-i', '--snowball-interval', help='set and save default year interval for snowball sampler '
                                                          'separated by hyphen (e. g. 1930-1967)', type=str)

    network = parser.add_argument_group('network modelling')
    network.add_argument('-c', '--coreset-sampler',
                         help='sample an predetermined initial set of publications from a provided list of ADS unique '
                              'identifiers (bibcodes), list must be provided as text file with one bibcode per line',
                         metavar='bibcode_list_filename')

    network.add_argument('-s', '--snowball-sampler',
                         help='sample new items from ADS based on the metadata of an initial set of items',
                         type=str, choices=['cit', 'ref', 'cit+ref'])

    network.add_argument('-e', '--edge-generator',
                         help='generate an edge list based on the metadata of an existing sample',
                         type=str, choices=['citnet', 'cocit', 'bibcp'])

    network.add_argument('-d', '--database',
                         help='SQLite database file name. If existing file provided, it will be edited, '
                         'otherwise a new file with that name will be created')

    network.add_argument('-m', '--modularity', help='assign a cluster ID to each node based '
                         'on the Community Infomap algorithm', action='store_true')

    return parser.parse_args()


def main():

    args = parse_args()
    home_dir = os.path.expanduser('~')
    conf_file = os.path.join(home_dir, '.ads2gephi/ads2gephi.cfg')

    # Check if config file available and if not, prompt for API Key and create config file
    if os.path.isfile(conf_file) == False:
        print("Please enter your API Key for the Astrophysical Data System (ADS). The key will be stored in a "
             "configuration file for future use. Please refer to the help text (-h) if you want to assign a new key.")
        key_input = input("API Key: ")
        conf_dir = os.path.join(home_dir, '.ads2gephi')
        os.makedirs(conf_dir)
        with open(conf_file, 'w+') as file:
            file.write("[ads_api]\n"
                              "apikey = {}\n\n"
                              "[snowball_default_interval]\n"
                              "startyear = 1900\n"
                              "endyear=2000".format(key_input))
            print("API Key has been set.")
            print("Default year interval for snowball sampling has been set to 1900-2000.")


    if args.version:
        print('0.1')

    if args.snowball_interval is not None:
        # Get year parameters from string
        start_year = args.snowball_interval[:4]
        end_year = args.snowball_interval[-4:]
        # Update config file
        config = ConfigParser()
        config.read_file(open(conf_file))
        config.set('snowball_default_interval', 'StartYear', start_year)
        config.set('snowball_default_interval', 'EndYear', end_year)
        with open(conf_file, 'w') as cp:
            config.write(cp)
        print("Default year interval for snowball sampling set to {}.".format(args.snowball_interval))

    if args.api_key is not None:
        # Update config file
        config = ConfigParser()
        config.read_file(conf_file)
        config['ads_api']['APIKey'] = args.api_key
        config.set('ads_api', 'APIKey', args.api_key)
        with open(conf_file, 'w') as cp:
            config.write(cp)

    citnet = CitationNetwork(args.database)
    citnet.parse_config(conf_file)

    if args.coreset_sampler:
        print('Starting core set (judgement) sampling...')
        with open(args.coreset_sampler) as file:
            for line in file:
                citnet.bibcode_list.append(line[:19])
        citnet.sample('judgement')

    if args.snowball_sampler == 'cit':
        print('Starting snowball sampling based on citation metadata...')
        citnet.snowball['scope'] = 'cit'
        citnet.sample('snowball')

    elif args.snowball_sampler == 'ref':
        print('Starting snowball sampling based on reference metadata...')
        citnet.snowball['scope'] = 'ref'
        citnet.sample('snowball')

    elif args.snowball_sampler == 'cit+ref':
        print('Starting snowball sampling based on citation and reference metadata...')
        citnet.snowball['scope'] = 'citref'
        citnet.sample('snowball')

    if args.edge_generator == 'citnet':
        print('Starting edge generator with regular citation network values...')
        citnet.make_regular_edges('bwd')

    elif args.edge_generator == 'cocit':
        print('Starting edge generator with co-citation values...')
        citnet.make_semsim_edges('cocit')

    elif args.edge_generator == 'bibcp':
        print('Starting edge generator with bibliographic coupling values...')
        citnet.make_semsim_edges('bibcp')


if __name__ == '__main__':
    main()
