from utils.parse_pipeline import parse_profiles_for_directory

# sample_profile_dir = '/home/sjb/Projects/Research/LinkedIn_OB/data/sample_data/828'
sample_profile_dir = '/media/sjb/Sandra M/SJ_Partition/unzipped/First_1000_0/111'

result = parse_profiles_for_directory(sample_profile_dir, from_zip=False, zf=None)
