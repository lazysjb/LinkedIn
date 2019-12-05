# Run file - lets later combine with run_raw_liwc_process
import os

from config import (
    LIWC_DISTANCE_SAVE_SUBDIR, LIWC_VECTOR_ROOT_DIR, LIWC_VECTOR_SAVE_SUBDIR
)
from liwc_utils.file_processor import process_liwc_distances


def main():
    liwc_vector_dir = os.path.join(LIWC_VECTOR_ROOT_DIR, LIWC_VECTOR_SAVE_SUBDIR)
    liwc_distance_dir = os.path.join(LIWC_VECTOR_ROOT_DIR, LIWC_DISTANCE_SAVE_SUBDIR)

    process_liwc_distances(liwc_vector_dir, liwc_distance_dir)


if __name__ == '__main__':
    main()
