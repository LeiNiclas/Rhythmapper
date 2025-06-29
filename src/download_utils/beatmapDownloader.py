import argparse
import os
import rateLimitOptimizer as rlo
import requests
import time


universal_request_headers = {
    "User-Agent": "Mozialla/5.0",
    "Accept": "application/json"
} 

parser = argparse.ArgumentParser()
parser.add_argument("--num_beatmapsets", type=int, default=0)
args = parser.parse_args()


def fetch_mania_beatmapset_IDs(amount_of_sets : int, page_offset : int) -> dict:
    """
    Retrieve a specific amount of beatmapset IDs
    and their corresponding children beatmap IDs.

    Args:
        amount_of_sets (int): _The amount of beatmapsets to retrieve at once._
        page_offset (int): _The page offset to retrieve beatmapsets from._

    Returns:
        dict: _A dictionary where each key is a beatmapset ID (int),
        and each value is a list of children beatmap IDs (list of int) belonging to that set._
    """
    
    # -------- Request --------
    url = f"https://osu.direct/api/search?mode=3&sort=ranked_date%3Adesc&amount={amount_of_sets}&status=1&offset={page_offset * amount_of_sets}"
    
    request = requests.get(url=url, headers=universal_request_headers)
    # -------------------------
    
    # -------- Beatmap ID retrieval --------
    if request.status_code == 200:
        response_json = request.json()
        
        beatmapset_IDs = {}
        
        for beatmapset in response_json:
            # The beatmapset ID is stored in the "SetID" entry.
            beatmapset_ID = beatmapset["SetID"]
            
            # The children beatmap IDs are store in the "ChildrenBeatmaps" entry.
            children_beatmap_IDs = beatmapset["ChildrenBeatmaps"]
            
            # Save the children beatmaps to a list that can be accessed by
            # using the beatmapset ID as a key to the dict of beatmap_IDs
            beatmapset_IDs[beatmapset_ID] = [ child_beatmap["BeatmapID"] for child_beatmap in children_beatmap_IDs ]
        
        # Handle request rate limit.
        time.sleep(rlo.get_optimal_wait_time(request=request))
        
        return beatmapset_IDs
    else:
        print(f"ERROR (beatmapDownloader.get_mania_beatmapset_IDs): Failed to get beatmap IDs: {request.status_code}\n")
        
        # Handle request rate limit.
        time.sleep(rlo.get_optimal_wait_time(request=request))
        
        return None
    # --------------------------------------


def download_beatmap(beatmap_ID : int, download_path : str, download_audio : bool = False) -> None:
    """
    Download the beatmap by its ID to the given download path.
    Optionally download the beatmap's audio. 

    Args:
        beatmap_ID (int): _The ID of the beatmap to download._
        download_path (str): _The target folder to download the map to._
        download_audio (bool, optional): _Should the audio file be downloaded as well?_ (Defaults to False)
    """
   
    # -------- Beatmap data request --------
    url = f"https://osu.direct/api/osu/{beatmap_ID}/raw"
    
    request = requests.get(url=url, headers=universal_request_headers)
    
    # Handle request rate limit.
    time.sleep(rlo.get_optimal_wait_time(request=request))
    # --------------------------------------
    
    # -------- File handling --------
    file_name = f"bm_{beatmap_ID}.osz"
    file_path = os.path.join(download_path, file_name)
    
    # We will need the name of the audio file (or rather - its extension)
    # to handle the download of it correctly. 
    audio_file_name = ""
    # -------------------------------
    
    # -------- Beatmap content --------
    if request.status_code == 200:
        response_content = request.content
        
        # Write the raw beatmap to the target folder.
        with open(file_path, "wb") as f:
            f.write(response_content)
        
        # Filter the audio file name from the beatmap file.
        str_content = str(response_content)
        
        if len(str_content.split("oFilename: ")) == 1:
            print(f"ERROR (beatmapDownloader.download_beatmap): " +
                  f"Failed to identify audio file name for beatmap with ID {beatmap_ID}")
            return
        
        audio_file_name_to_end = str_content.split("oFilename:")[1]
        audio_file_name = audio_file_name_to_end.split('\\')[0].strip()
    else:
        print(f"ERROR (beatmapDownloader.download_beatmap): " +
              f"Failed to download beatmap with ID {beatmap_ID}: {request.status_code}")
        return
    # ---------------------------------
    
    if not download_audio:
        return
    
    # -------- Beatmap audio request --------
    url = f"https://osu.direct/api/media/audio/{beatmap_ID}/download"
    
    request = requests.get(url=url, headers=universal_request_headers)
    
    # Handle request rate limit.
    time.sleep(rlo.get_optimal_wait_time(request=request))
    # ---------------------------------------
    
    # -------- Beatmap audio --------
    if request.status_code == 200:
        # Uniformly name the audio file "audio" and add the extension.
        audio_file_extension = audio_file_name.split(".")[-1]
        audio_file_name = "audio." + audio_file_extension
        audio_file_path = os.path.join(download_path, audio_file_name)
        
        # Write the audio file to the target folder.
        with open(audio_file_path, "wb") as f:
            f.write(request.content)
        
        return
    else:
        print(f"ERROR (beatmapDownloader.download_beatmap): Failed to download audio for beatmap {beatmap_ID}: {request.status_code}")
        return
    # -------------------------------


def batch_download_beatmaps(amount_of_sets : int, page_offset : int, download_folder_path : str) -> None:
    mania_beatmapset_IDs = fetch_mania_beatmapset_IDs(amount_of_sets=amount_of_sets, page_offset=page_offset)
    
    if mania_beatmapset_IDs is None:
        print("ERROR (beatmapDownloader.batch_download_beatmaps): Failed to fetch beatmaps.")   
        return

    print(f"{8*'='} beatmapDownloader.batch_download_beatmaps {8*'='}")
    print(f"Starting download of {amount_of_sets} beatmapsets from page {page_offset + 1}...")
    print(f"{59*'-'}")
    
    for beatmapset_ID, beatmap_IDs in mania_beatmapset_IDs.items():
        # Always download the audio file for the first beatmap in the set.
        # For the overwhelming majority of ranked beatmaps,
        # all children beatmaps share the same audio file.
        download_audio = True
        
        download_path = os.path.join(download_folder_path, f"bmset_{beatmapset_ID}")
        
        # Skip beatmapset if a folder with its name already exists.
        if (os.path.exists(download_path)):
            print(f"Skipping beatmapset with ID {beatmapset_ID} (Beatmapset already exists in download folder).")    
            continue
        
        os.mkdir(download_path)
        
        print(f"Downloading beatmapset with ID {beatmapset_ID}...", end='\r', flush=True)
        
        for i, beatmap_ID in enumerate(beatmap_IDs):
            download_beatmap(beatmap_ID=beatmap_ID, download_path=download_path, download_audio=download_audio)
            
            # After the first beatmap, another download of the audio file is not needed.
            download_audio = False
            
            progress = f"Downloading beatmapset with ID {beatmapset_ID}... ({i+1}/{len(beatmap_IDs)} beatmaps downloaded)"
            print(progress, end='\r', flush=True)
        
        print(80 * ' ', end='\r')
        print(f"Download of beatmapset with ID {beatmapset_ID} finished. ({len(beatmap_IDs)}/{len(beatmap_IDs)})")
    
    print(f"{59*'-'}")
    print(f"Download of {amount_of_sets} beatmapsets from page {page_offset + 1} finished.")
    print(f"{59*'='}\n")


def main():
    if not args.num_beatmapsets:
        return
    
    download_folder = os.path.join(os.getcwd(), "data", "raw")
    
    os.makedirs(download_folder, exist_ok=True)
    os.system('cls' if os.name == 'nt' else 'clear')
    
    num_batches = args.num_beatmapsets // 100
    
    for i in range(num_batches):
        batch_download_beatmaps(args.num_beatmapsets // 10, i, download_folder)


if __name__ == "__main__":
    main()
