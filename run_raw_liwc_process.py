# Run file
import os

import click
import pandas as pd

from config import LIWC_VECTOR_ROOT_DIR
from liwc_utils.file_processor import process_liwc_source_df


@click.command()
@click.option('--liwc_source_filename', default='LIWC_individual_company_mapped_no_walmart.csv')
def main(liwc_source_filename):
    source_filepath = os.path.join(LIWC_VECTOR_ROOT_DIR, liwc_source_filename)
    liwc_df = pd.read_csv(source_filepath)
    process_liwc_source_df(liwc_df, verbose=False)


if __name__ == '__main__':
    main()
