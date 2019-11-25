# Run file
import click

from utils.db_util import create_postgres_engine
from utils.post_parse_process_util import run_parsed_to_db


@click.command()
@click.option('--batch_dir', required=True)
def main(batch_dir):
    print('Saving parsed contents in {} to DB'.format(batch_dir))
    db_conn = create_postgres_engine()
    run_parsed_to_db(batch_dir,
                     db_conn,
                     run_education=True,)


if __name__ == '__main__':
    main()
