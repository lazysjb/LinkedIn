import os


def zipdir(path, zf_handle, truncate_arcname=True):
    """Recursively zip contents of path to zf_handle

    if truncate_arcname is True, only include immediate parent of
    filename only
    """
    uniq_parent_dirs = set()

    for root, dirs, files in os.walk(path):
        for file in files:
            if truncate_arcname:
                if not len(file):
                    continue
                else:
                    parent = root.split('/')[-1]
                    file_path_in_archive = os.path.join(parent, file)
                    # Just for info printing
                    if parent not in uniq_parent_dirs:
                        uniq_parent_dirs.add(parent)
                        print('Starting to archive parent {}'.format(parent))
            else:
                file_path_in_archive = os.path.join(root, file)

            zf_handle.write(os.path.join(root, file), arcname=file_path_in_archive)
