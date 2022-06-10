from glob import glob
from argparse import ArgumentParser
from os.path import basename, isfile
from os import remove
from datetime import timedelta
from visiannot.tools.video_loader import get_duration_video
from visiannot.tools.datetime_converter import get_datetime_from_path


######################
# script starts here #
######################

parser = ArgumentParser()

parser.add_argument(
    "video_dir",
    type=str,
    help="Path to directory with video recording"
)

args, _ = parser.parse_known_args()
video_dir = args.video_dir

timestamp_format = "%Y-%m-%dT%H:%M:%S.%f"

# initialize output path
output_path = None

# get list of video paths
vid_path_list = sorted(glob("%s/*BW1*.mp4" % video_dir))

# loop on paths
for path in vid_path_list:
    beg_datetime = get_datetime_from_path(path, '_', 1, "%Y-%m-%dT%H-%M-%S")
    duration = get_duration_video(path)

    end_datetime = beg_datetime + timedelta(seconds=duration)

    # convert datetime to string
    beg_string = beg_datetime.strftime(timestamp_format)
    end_string = end_datetime.strftime(timestamp_format)

    # get output path
    if output_path is None:
        base_name_split = basename(path).split('_')
        output_path = "%s_%s_DURATION-datetime.txt" % (base_name_split[0], base_name_split[1])

        if isfile(output_path):
            remove(output_path)

    # write annotation file
    with open(output_path, 'a') as f:
        f.write("%s - %s\n" % (beg_string, end_string)) 