import os
import sys
import click
from ads import SearchQuery
from ads.base import APIResponseError
from configparser import ConfigParser
from yaspin import yaspin


@click.command()
@click.version_option(version='0.1.2')
@click.option(
    '--coreset-sampler', '-c',
    type=click.File(),
    help='Sample an predetermined initial set of publications from a provided list of ADS '
         'unique identifiers (bibcodes). The list must be provided as a text file with one bibcode per line.'
)
@click.option(
    '--snowball-sampler', '-s',
    type=click.Choice(['cit', 'ref', 'cit+ref']),
    help='Sample new items from ADS based on the metadata of an initial set of items.'
)
@click.option(
    '--edge-generator', '-e',
    type=click.Choice(['citnet', 'cocit', 'bibcp']),
    help='Generate an edge list based on the metadata of an existing sample.'
)
@click.option(
    '--database', '-d',
    default='ads2gephi_sqlite.db',
    help='SQLite database file name. If an existing file is provided, it will be edited, '
         'otherwise a new file with that name will be created.'
)
@click.option(
    '--modularity', '-m',
    is_flag=True,
    help='Assign a cluster ID to each node based on the Community Infomap algorithm.'
)
def main(coreset_sampler, snowball_sampler, edge_generator, database, modularity):

    # CONFIGURATION
    home_dir = os.path.expanduser('~')
    conf_dir_path = os.path.join(home_dir, '.ads2gephi')
    conf_file_path = os.path.join(conf_dir_path, 'ads2gephi.cfg')
    if os.path.isfile(conf_file_path):
        print(f'Found configuration file: {conf_file_path}')
    else:
        print(f'Please enter your API Key for the Astrophysical Data System (ADS) and the year values for '
              f'the snowball sampling time interval.\nThe API key and year interval will be stored in a '
              f'configuration file ({conf_file_path}) for future use.\nFeel free to edit this file if you '
              f'want to assign new values.')
        key_input = click.prompt('API Key', type=str)
        start_year = click.prompt('Start year', type=str, default='1900')
        end_year = click.prompt('End year', type=str, default='2000')
        os.makedirs(conf_dir_path, exist_ok=True)
        try:
            SearchQuery(
                bibcode='1968IAUS...29...11A',
                token=key_input
            ).next()
        except APIResponseError as error:
            click.secho('[ERROR]', fg='red', bold=True)
            sys.exit(f'[ERROR] The ADS API refused the key you provided: \n\t{error}')

        with open(conf_file_path, 'w+') as file:
            file.write(f'[ads_api]\n'
                       f'apikey = {key_input}\n\n'
                       f'[snowball_default_interval]\n'
                       f'startyear={start_year}\n'
                       f'endyear={end_year}')
            print('API Key has been set.')
            print(f'Default year interval for snowball sampling '
                  f'has been set to {start_year}-{end_year}.')

    config = ConfigParser()
    config.read_file(open(conf_file_path))
    config_start_year = config['snowball_default_interval']['StartYear']
    config_end_year = config['snowball_default_interval']['EndYear']

    from ads2gephi.ads2gephi import Database

    # DATA PROCESSING
    loading_message = f'Loading database from {database}'
    with yaspin(text=loading_message) as spinner:
        db = Database(database)
        db.read_citnet_from_db()
        citnet = db.citnet
        spinner.ok(u'\u2713')
    if coreset_sampler:
        loading_message = f'Sampling nodes from ' \
                          f'bibcodes provided in {coreset_sampler.name}'
        with yaspin(text=loading_message) as spinner:
            with coreset_sampler as file:
                citnet.sample_judgement(
                    [line for line in file]
                )
            spinner.ok(u'\u2713')
    if snowball_sampler == 'cit':
        print('Starting snowball sampling based on citation metadata')
        citnet.sample_snowball(
            year_interval=(config_start_year, config_end_year),
            scope='cit'
        )
    elif snowball_sampler == 'ref':
        print('Starting snowball sampling based on reference metadata')
        citnet.sample_snowball(
            year_interval=(config_start_year, config_end_year),
            scope='ref'
        )
    elif snowball_sampler == 'cit+ref':
        print('Starting snowball sampling based on citation and reference metadata')
        citnet.sample_snowball(
            year_interval=(config_start_year, config_end_year),
            scope='cit+ref'
        )
    if edge_generator == 'citnet':
        loading_message = 'Starting edge generator with regular citation network values'
        with yaspin(text=loading_message) as spinner:
            citnet.make_regular_edges()
            spinner.ok(u'\u2713')
    elif edge_generator == 'cocit':
        loading_message = 'Starting edge generator with co-citation values'
        with yaspin(text=loading_message) as spinner:
            citnet.make_semsim_edges('cocit')
            spinner.ok(u'\u2713')
    elif edge_generator == 'bibcp':
        loading_message = 'Starting edge generator with bibliographic coupling values'
        with yaspin(text=loading_message) as spinner:
            citnet.make_semsim_edges('bibcp')
            spinner.ok(u'\u2713')
    if modularity:
        loading_message = 'Initiating modularity assignment'
        with yaspin(text=loading_message) as spinner:
            citnet.assign_modularity()
            spinner.ok(u'\u2713')

    loading_message = f'Writing citation network to {database}'
    with yaspin(text=loading_message) as spinner:
        db.write_citnet_to_db()
        spinner.ok(u'\u2713')


if __name__ == '__main__':
    main()
