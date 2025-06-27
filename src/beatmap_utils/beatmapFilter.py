from ..download_utils import rateLimitOptimizer as rlo
import requests
import time


universal_request_headers = {
    "User-Agent": "Mozialla/5.0",
    "Accept": "application/json"
}


def get_beatmap_metadata(beatmap_ID : int) -> dict:
    """
    Retrieve the JSON metadata for a specific beatmap.

    Args:
        beatmap_ID (int): _The ID of the beatmap to get the metadata from._

    Returns:
        dict: _dict of the JSON contents of beatmap metadata if successful._ Defaults to None
    """
    
    url = f"https://osu.direct/api/b/{beatmap_ID}"
    
    session = requests.Session()
    session.headers.update(universal_request_headers)
    
    request = session.get(url)
    
    # Handle request rate limit.
    time.sleep(rlo.get_optimal_wait_time(request=request))
    
    if request.status_code == 200:
        return request.json()
    else:
        print("ERROR (beatmapFilter.get_beatmap_metadata): "
              + f"Failed to fetch beatmap metadata for beatmap with ID {beatmap_ID}")
        return None


def get_beatmap_difficutly(metadata_json) -> str:
    """
    Retrieve the difficulty rating of a beatmap through its metadata.

    Args:
        metadata_json (dict): _The JSON metadata of a given beatmap._

    Returns:
        str: _Difficulty range label._
    """
    difficulty_rating = metadata_json["DifficultyRating"]

    if difficulty_rating < 1.0:
        return "0-1_stars"
    elif difficulty_rating < 2.0:
        return "1-2_stars"
    elif difficulty_rating < 3.0:
        return "2-3_stars"
    elif difficulty_rating < 4.0:
        return "3-4_stars"
    elif difficulty_rating < 5.0:
        return "4-5_stars"
    else:
        return "5_stars_plus"


def beatmap_is_Nk(metadata_json, N : int) -> bool:
    """
    Check if the beatmap is Nk (N-keys) through its metadata.

    Args:
        metadata_json (dict): _The JSON metadata of a given beatmap._
        N (int): _The amount of keys used. Also known as "CircleSize" [CS]._

    Returns:
        bool: _True_, if beatmap is Nk and the mode is mania (Mode = 3). _False_ otherwise.
    """
    circle_size = metadata_json["CS"]
    mode = metadata_json["Mode"]
    
    return circle_size == N and mode == 3


def filter_beatmap(beatmap_ID : int, keys : int) -> tuple[bool, str]:
    """
    Checks a beatmap for difficulty and key count.

    Args:
        beatmap_ID (int): _The ID of the beatmap to filter._
        keys (int): _The amount of keys used. Also known as "CircleSize" [CS]._

    Returns:
        _type_: _description_
    """
    beatmap_metadata = get_beatmap_metadata(beatmap_ID=beatmap_ID)
    
    if beatmap_metadata is None:
        return
    
    beatmap_difficulty = get_beatmap_difficutly(metadata_json=beatmap_metadata)
    beatmap_fits_criteria = beatmap_is_Nk(metadata_json=beatmap_metadata, N=keys)

    return beatmap_fits_criteria, beatmap_difficulty
