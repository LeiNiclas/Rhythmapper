from ..download_utils import rateLimitOptimizer as rlo
import requests
import time
import dotenv
import os
from ossapi import Ossapi, Beatmap


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
    
    # REWORK!!! -------------------------------------
    env_path = os.path.join(os.getcwd(), ".env")
    dotenv.load_dotenv(env_path)
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    api = Ossapi(client_id, client_secret)
        
    metadata = api.beatmap(beatmap_id=beatmap_ID)

    if not metadata:
        print("ERROR (beatmapFilter.get_beatmap_metadata): "
              + f"Failed to fetch beatmap metadata for beatmap with ID {beatmap_ID}")
        return None
    
    return metadata
    # -----------------------------------------------


def get_beatmap_difficutly(beatmap_metadata : Beatmap) -> str:
    """
    Retrieve the difficulty rating of a beatmap through its metadata.

    Args:
        metadata_json (dict): _The JSON metadata of a given beatmap._

    Returns:
        str: _Difficulty range label._
    """
    difficulty_rating = beatmap_metadata.difficulty_rating

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


def beatmap_is_Nk(beatmap_metadata : Beatmap, N : int) -> bool:
    """
    Check if the beatmap is Nk (N-keys) through its metadata.

    Args:
        metadata_json (dict): _The JSON metadata of a given beatmap._
        N (int): _The amount of keys used. Also known as "CircleSize" [CS]._

    Returns:
        bool: _True_, if beatmap is Nk and the mode is mania (Mode = 3). _False_ otherwise.
    """
    circle_size = beatmap_metadata.cs
    mode = beatmap_metadata.mode_int
    
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
        return False, "ERROR"
    
    beatmap_difficulty = get_beatmap_difficutly(beatmap_metadata=beatmap_metadata)
    beatmap_fits_criteria = beatmap_is_Nk(beatmap_metadata=beatmap_metadata, N=keys)

    return beatmap_fits_criteria, beatmap_difficulty
