# Run file
from config import SOURCE_DATA_DIR
from utils.parse_pipeline import run_parse_pipeline


def main():
    run_parse_pipeline(root_dir=SOURCE_DATA_DIR)


if __name__ == '__main__':
    main()
