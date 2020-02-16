import json
import logging
import operator
import os
import random
import requests
import time

log = logging.getLogger()

def error_message(error_type, location, file_location = "derpi_get/core_class.py"):
    """
    Creates a custom error message.
    ---
    :param <error_type>: <str> ; short description of occuring error
    :param <location>: <str> ; name of method where the error occured
    """
    return f"An {error_type} error was raised in the {location} method of the class img_metadata"+\
        f"in the {file_location} file."

class img_metadata:
    """
    Object implementing how to retrieve picture metadata from derpibooru's
    REST API. Data is retrieved as a series of c. 1Mb JSON files.
    """
    def __init__(self, tags = [], at_least_one = True, instances = 10):
        """
        Initializes the img_metadata class object.
        ---
        :param <tags>: <list> ; list picture tags used for sorting and extracting metadata
        :param <at_least_one>: <boolean> ; toggles whether or not data to be retrieved must satisfy at least one tag or all of them
        :param <instances>: <integer> ; number of derpibooru image requests allowed before stopping
        """      
        assert(isinstance(tags, list)), error_message("Erroneous Type", "__init__")
        assert((isinstance(instances, int)) or instances == ""), error_message("Erroneous Type", "__init__")
        assert(isinstance(at_least_one, bool)), error_message("Erroneous Type", "__init__")
        
        self.tags = tags
        self.at_least_one = at_least_one
        self.instances = instances
    
    def bytes_length(self, bytes_size):
        """
        Calculates byte length of a file, based on the assumption that the file will not exceed 1,000Tb in size.
        ---
        :param <bytes_size>: <integer> ; size in bytes of a file
        """
        assert(isinstance(bytes_size, float)), error_message("Erroneous Type", "bytes_length")
        for unit_multiple in ["bytes", "KB", "MB", "GB", "TB"]:
            if bytes_size < 1024.0: return f"{round(bytes_size, 2)} {unit_multiple}"
            bytes_size /= 1024.0
    
    def keys_to_keep(self):
        """
        Returns the keys to be kept in the extracted JSON data.
        List of keys available:
        {"id", "created_at", "updated_at", "first_seen_at", "tags", "tag_ids", "uploader_id",
        "score", "comment_count", "width", "height", "tag_count", "file_name", "description",
        "uploader", "image", "upvotes", "downvotes", "faves", "aspect_ratio", "original_format",
        "mime_type", "sha512_hash", "orig_sha512_hash", "source_url", "representations", 
        "is_rendered", "is_optimized", "interactions", "spoilered"}
        """
        keys_to_keep = ["id", "created_at", "updated_at", "score", "uploader",
                        "uploader_id", "upvotes", "downvotes", "faves", "tags",
                        "tags_id", "aspect_ratio", "representations"]
        return keys_to_keep
    
    def json_split_size(self, path):
        """
        Splits a json file if it is too large (>1Mb).
        ---
        :param <path>: <string> ; path of a json file to weigh
        """
        assert(isinstance(path, str)), error_message("Erroneous Type", "json_split_size")
        max_size_reached_message = "MAX JSON FILE SIZE REACHED: file to be split."

        length = self.bytes_length(float(os.stat(path).st_size))
        length = length.split(" ")

        if float(length[0]) >= 1.0 and length[1] == "MB":
            nb_file = 0
            while True:
                new_path = path[:-5] + "_" + str(nb_file) + ".json"
                nb_file += 1
                if os.path.exists(new_path) == False:
                    print(max_size_reached_message)
                    try:
                        os.rename(path, new_path)
                    except (IOError, WindowsError):
                        log.error(error_message("IO or Windows", "json_split_size"))
                        raise
                    break
            return True
        else:
            return False

    def check_prior_extract(self, print_msg = True):
        """
        Checks if prior JSON extractions exist in the working directory (possibly created by self.json_split_size()
        The default file name is 'derpibooru_metadata.json'.
        ---
        :param <print_msg>: <boolean> ; toggles between printing messages to the cmd or printing nothing
        """
        
        def create_warnings(file):
            """
            Creates a dictionary of warning messages related to file management.
            ---
            :param <file>: <str> ; name of item.
            """
            return {"created":f"{file} created in {os.getcwd()}.",
            "not_created":f"{file} not created in {os.getcwd()}.",
            "found":f"{file} found in {os.getcwd()}.",
            "not_found":f"{file} not found in {os.getcwd()}."}

        assert(isinstance(print_msg, bool)), error_message("Erroneous Type", "check_prior_extract")        
        
        folder_messages = create_warnings("Folder ./data")
        json_messages = create_warnings("File derpibooru_metadata.json")
        json_path = os.getcwd() + "\\data\\derpibooru_metadata.json"
        
        # Checks if a json file exists
        if os.path.exists(json_path):
            if print_msg: print(json_messages["found"])
        else:
            # If the json file doesn't exist, checks if the folder ./data exists
            # If the folder doesn't exist, creates it
            try:
                if print_msg: print(json_messages["not_found"])
                if not os.path.exists(os.getcwd() + "\\data"):
                    if print_msg: print(folder_messages["not_found"])
                    os.makedirs(os.getcwd() + "\\data")
                    if print_msg: print(folder_messages["created"])
                with open(json_path, "w") as file: file.write("[]")
                if print_msg: print(json_messages["created"])
            except (IOError, WindowsError) as error:
                if print_msg: print(folder_messages["not_created"]+"\n"+json_messages["not_created"])
                log.error(error_message("IO or Windows", "check_prior_extract"))
                raise
        return json_path

    def crawl_metadata(self):
        """
        Retrieves picture metadata from the derpibooru REST API.
        """
        
        def back_off(counter, error):
            """
            In case of a request error, creates a back-off as requested by the derpibooru ToS.
            ---
            :param <counter>: int ; counter variable
            :param <error>: str ; error message
            """
            if counter > 50: 
                log.error(error)
                raise
            print(f"The program will back off for {2**counter} seconds.")
            counter += 1
            time.sleep(2 ** counter)
            return counter
        
        derpibooru_url = "https://derpibooru.org/images.json?constraint=id&order=a&gt="
        iterations = self.instances
        back_off_counter = 0
        
        # Checks for prior extractions
        try: json_path = self.check_prior_extract()
        except (IOError, WindowsError) as error:
            log.error(error_message("IO or Windows", "crawl_metadata"))
            raise
        
        # Saves existing data in the most recent JSON file
        with open(json_path, "r") as file: requested_id = json.load(file)
        json_local = requested_id
        # Records the most recent retrieved ID (+&) based on the assumption that the JSON is sorted in descending order
        if requested_id == []: requested_id = 1
        else: requested_id = requested_id[0]["id"] + 1

        while True:
            try:
                # Checks if iterations is a variable of type int
                # If it is, subtracts 1 (iterations is a counter)
                if type(iterations)==int:
                    if iterations > 0: iterations -= 1
                    else: 
                        print(f"{self.instances} images retrieved as requested.")
                        break
                # Checks if ./data folder and target metadata file exist
                json_path = self.check_prior_extract(False)
                # Requests a new derpibooru page
                print(f"You are requesting the derpibooru page starting with the id° {requested_id}.")
                json_derpibooru = requests.get(derpibooru_url + str(requested_id)).json()["images"]
                # Raises exception in case derpibooru was fully scraped, i.e. request returned an empty list
                if json_derpibooru == []: raise DatabaseFullyCrawled
                # Updates content of metadata file
                requested_id, json_local = self.json_collect(json_derpibooru, json_local, json_path)
                #time delay to respect the API's license
                time.sleep(.200)
            except DatabaseFullyCrawled:
                print("The crawler scraped the derpibooru metadata. The program will now close.")
                break
            except (IOError, WindowsError):
                back_off_counter = back_off(back_off_counter, error_message("IO or Windows", "crawl_metadata"))
            except (requests.exceptions.TooManyRedirects, requests.exceptions.RequestException):
                back_off_counter = back_off(back_off_counter, error_message("Request [generic error]", "crawl_metadata"))
            except requests.exceptions.HTTPError:
                back_off_counter = back_off(back_off_counter, error_message("Request [hhtp]", "crawl_metadata"))
            except requests.exceptions.ConnectionError:
                back_off_counter = back_off(back_off_counter, error_message("Request [Connection]", "crawl_metadata"))
            except requests.exceptions.Timeout:
                back_off_counter = back_off(back_off_counter, error_message("Request [timeout]", "crawl_metadata"))  

    def json_collect(self, json_derpibooru, json_local, json_path):
        """
        Stores a json file for later use with a specific numbered name when its size reaches
		1Mb. Storing is performed by renaming the target file.
        ---
        :param <json_derpibooru>: <json_object> ; JSON data extracted from derpibooru
        :param <json_local>: <json_object> ; JSON data stored locally
        :param <json_path>: <string> ; path of local file where the data is stored
        """
        stored_keys = self.keys_to_keep()
        last_id = -1
        
        # Sorts metadata by ID
        for image_data in json_derpibooru:
            temp = image_data.copy()
            # Deletes unwanted keys from each JSON entry
            for item in image_data: 
                if item not in stored_keys: del temp[item]
            last_id = max(image_data["id"], last_id)
            json_local.append(temp)
            json_local.sort(key=operator.itemgetter("id"), reverse = True)
        # Saves the JSON
        with open(json_path,'w') as file: json.dump(json_local, file)
        
        # Tests if the JSON is too large and needs to be split
        try: split = self.json_split_size(json_path)
        except (IOError, WindowsError) as error:
            log.error(error_message("IO or Windows", "json_collect"))
            raise
        if split == True: json_local = []
        return last_id, json_local
    
    def id_filter(self, tags, at_least_one):
        """
        Retrieves the IDs of the locally stored metadata that fit specific tag parameters
        ---
        :param <tags>: <list> ; list picture tags used for sorting and extracting metadata
        :param <at_least_one>: <boolean> ; toggles whether or not data to be retrieved must satisfy at least one tag or all of them
        """
        
        def any_or_all(boolean):
            """
            Returns the function any() if argument <boolean> TRUE, else returns function all()
            ---
            :param <boolean>: <boolean> ; boolean value
            """
            if boolean == True: return any
            else: return all
        
        metadata_files_list = filter(lambda file: file.startswith("derpibooru_metadata"), os.listdir(os.getcwd() + "\\data"))
        metadata_files_list = list(metadata_files_list)
        id_list = []
        url_list = []
        
        for fname in metadata_files_list:
            try:
                with open(os.getcwd() + "\\data\\" + fname,"r") as file: json_local = json.load(file)
                if json_local == []: break
                # Creates a list of the tags to keep based on each starting with a key character +
                tags_keep = list(filter(lambda item: item.startswith("+"), tags))
                tags_keep = list(map(lambda item: item[1:], tags_keep))
                # Creates a list of the tags to keep based on each starting with a key character -
                tags_remove = list(filter(lambda item: item.startswith("-"), tags))
                tags_remove = list(map(lambda item: item[1:], tags_remove))
                # Checks the requested filter
                fltr = any_or_all(at_least_one)
                # Filters out unwanted entries
                filter_keep = lambda item: fltr(tag in item["tags"].split(", ") for tag in tags_keep)
                filter_remove = lambda item: not any(tag in item["tags"].split(", ") for tag in tags_remove)
                json_kept = list(filter(filter_keep, json_local))
                json_kept = list(filter(filter_remove, json_kept))
                filter_id = lambda item: item["id"]
                filter_url = lambda item: item["representations"]["medium"][2:]
                id_list += list(map(filter_id, json_kept))
                url_list += list(map(filter_url, json_kept))
            except (IOError, WindowsError) as error:
                log.error(error_message(f"{fname} JSON - IO or Windows", "id_filter"))
                raise
        
        return list(zip(id_list, url_list))
    
    def repair_tags(self):
        """
        Checks if all retrieved IDs have an available list of tags.
        If not, repairs them by requested the derpibooru's API.
        """
        metadata_files_list = filter(lambda file: file.startswith("derpibooru_metadata"), os.listdir(os.getcwd() + "\\data"))
        metadata_files_list = list(metadata_files_list)
        
        for fname in metadata_files_list: 
            with open(os.getcwd() + "\\data\\" + fname, "r") as file: 
                try:
                    json_local = json.load(file)
                    if json_local == []: break
                    for index, item in enumerate(json_local):
                        if item["tags"] == None:
                            json_id = item["id"]
                            path_derpibooru = "https://derpibooru.org/" + str(json_id) + ".json"
                            json_derpibooru = requests.get(path_derpibooru).json()
                            time.sleep(.200)
                            if json_derpibooru["tags"] == None: raise AbsentTagList
                            json_local[index]["tags"] = json_derpibooru["tags"]
                            print(f"The tags of the picture {json_id} were updated.") 
                except AbsentTagList:
                    print(f"The url request for the picture {json_id} returned an empty list of tags.")
                except (IOError, WindowsError) as error:
                    log.error(error_message("IO or Windows", "repair_tags"))
                    raise
                except (requests.exceptions.TooManyRedirects, requests.exceptions.RequestException) as error:
                    log.error(error_message("Request [generic error]", "repair_tags"))
                    raise
                except requests.exceptions.HTTPError as error:
                    log.error(error_message("Request [hhtp]", "repair_tags"))
                    raise
                except requests.exceptions.ConnectionError as error:
                    log.error(error_message("Request [Connection]", "repair_tags"))
                    raise
                except requests.exceptions.Timeout as error:
                    log.error(error_message("Request [timeout]", "repair_tags"))
                    raise
            try:
                with open(os.getcwd() + "\\data\\" + fname,'w') as file: json.dump(json_local, file)
            except (IOError, WindowsError) as error:
                log.error(error_message("IO or Windows", "repair_tags"))
                raise

class Error(Exception):
    """Base class for other exceptions"""
    pass

class DatabaseFullyCrawled(Error):
    """Raised when the crawler reached the last pages of derpibooru"""
    pass

class AbsentTagList(Error):
    """Raised when the key value of the key 'tags' in a dictionary is 'None'"""
    pass