import os
import json
import sys
from datetime import datetime, timezone
import win32file
import win32con
import glob

def modify_time(file_path, timestampcreated, timestampmodified):
    dt = datetime.fromtimestamp(timestampcreated, tz=timezone.utc)
    dtc = datetime.fromtimestamp(timestampmodified, tz=timezone.utc)
    handle = win32file.CreateFile(
        file_path,
        win32file.GENERIC_WRITE,
        0,
        None,
        win32con.OPEN_EXISTING,
        win32con.FILE_ATTRIBUTE_NORMAL,
        None
    )
    win32file.SetFileTime(handle, dt, None, dtc)
    handle.close()

def get_timestampcreated(data):
    if 'photoTakenTime' in data and 'timestamp' in data['photoTakenTime']:
        return int(data['photoTakenTime']['timestamp'])
    elif 'created' in data:
        date_str = data['created']
        if '.' not in date_str:
            dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        else:
            dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        return int(dt.timestamp())
    else:
        raise KeyError("No valid timestamp found in JSON data")

def get_timestampmodified(data):
    if 'creationTime' in data and 'timestamp' in data['creationTime']:
        return int(data['creationTime']['timestamp'])
    elif 'content_last_modified' in data:
        date_str = data['content_last_modified']
        if '.' not in date_str:
            dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        else:
            dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        return int(dt.timestamp())
    else:
        raise KeyError("No valid timestamp found in JSON data")

def process_file(directory, filename):
    jpg_path = os.path.join(directory, filename)

    base_filename, ext = os.path.splitext(filename)

    # Search for any JSONs that start with the image name (with extension or without)
    patterns = [
        os.path.join(directory, f"{filename}*.json"),       # IMG_0085(1).PNG*.json
        os.path.join(directory, f"{base_filename}*.json")   # IMG_0085(1)*.json
    ]

    json_candidates = []
    for pat in patterns:
        json_candidates.extend(glob.glob(pat))

    for json_path in json_candidates:
        try:
            with open(json_path, 'r') as json_file:
                data = json.load(json_file)
                timestampcreated = get_timestampcreated(data)
                timestampmodified = get_timestampmodified(data)
                modify_time(jpg_path, timestampcreated, timestampmodified)
                print(f"Updated {jpg_path} with timestamp {timestampcreated}")
            
            os.remove(json_path)
            print(f"Removed {json_path}")
            break  # stop after first good JSON
        except Exception as e:
            print(f"Failed to process {json_path}: {e}")
            continue

def process_directory(directory, recursive=False):
    for root, _, files in os.walk(directory):
        for filename in files:
            try:
                if not filename.lower().endswith('.json'):
                    process_file(root, filename)
            except Exception as e:
                print(f"Failed to process {filename} in {root}: {e}")
                sys.exit()
        if not recursive:
            break

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python windows.py <directory_path1> <directory_path2> ...")
    else:
        recursive = input("Do you want to search all subdirectories? (y/n): ").strip().lower() == 'y'
        
        for directory in sys.argv[1:]:
            if os.path.isdir(directory):
                process_directory(directory, recursive)
            else:
                print(f"The path '{directory}' is not a valid directory.")
