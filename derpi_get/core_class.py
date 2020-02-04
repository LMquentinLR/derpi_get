import json
import logging
import operator
import os
import random
import requests
import time

log = logging.getLogger()

def error_message(error_type, location):
    """
    Creates a custom error message.
    ---
    :param <error_type>: <str> ; type of occuring error
    :param <location>: <str> ; method name where the error occured
    """
    return f"An {error_type} error was raised in the {location} method of the class img_metadata"+\
        "in the derpi_get/core_class.py file."

class img_metadata:
    """
    Class object that describes how to retrieve picture metadata from derpibooru's
    REST API. Data is retrieved as a series of c. 1Mb JSON files.
    """
    def __init__(self, tags = [], at_least_one = True, instances = 10):
        """
        Initializes of the img_metadata class object.
        ---
        :param <tags>: <list> ; list of strings (i.e. picture tags)
        :param <at_least_one>: <boolean> ; toggles 'at least one tag' option instead of 'all tags'
        :param <instances>: <integer> ; number of instances/loops allowed before stop
        """      
        assert(not isinstance(tags, list)), error_message("Erroneous Type", "__init__")
        assert(not isinstance(instances, int)), error_message("Erroneous Type", "__init__")
        assert(not isinstance(at_least_one, bool), error_message("Erroneous Type", "__init__")
        self.tags = tags
        self.at_least_one = at_least_one
        self.instances = instances
    
    def bytes_length(self, bytes_size):
        """
        Calculates byte length of a file, based on the assumption that the file will not exceed 1,000Tb in size.
        ---
        :param <bytes_size>: <integer> ; size in bytes of a file
        """
        assert(not isinstance(bytes_size, float)), error_message("Erroneous Type", "bytes_length")
        for unit_multiple in ['bytes', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0: return "%3.1f %s" % (bytes_size, unit_multiple)
            bytes_size /= 1024.0
    
    def keys_to_keep(self):
        """
        Returns the keys to keep in the extracted JSON data.
        keys available:
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
        Splits a json file if it is too large (1Mb).
        ---
        :param <path>: <string> ; path of a json file to weigh
        """
        assert(not isinstance(path, str)), error_message("Erroneous Type", "json_split_size")
        max_size_reached_message = "JSON MAX FILE SIZE REACHED: JSON file to be archived and a new one created."

        length = self.bytes_length(float(os.stat(path).st_size))
        length = length.split(" ")

        if float(length[0]) >= 1.0 and length[1] == "MB":
            nb_file = -1
            while True:
                nb_file += 1
                new_path = path[:-5] + "_" + str(nb_file) + ".json"
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
        :param <print_msg>: <boolean> ; toggle between 'prints message to command line' and 'prints nothing'
        """
        def create_messages(item):
            """
            Creates a dictionary of warning messages.
            ---
            :param <item>: <str> ; name of item.
            """
            return {"created":f"{item} created in {os.getcwd()}.",
            "not_created":f"{item} not created in {os.getcwd()}.",
            "found":f"{item} found in {os.getcwd()}.",
            "not_found":f"{item} not found in {os.getcwd()}."}

        assert(not isinstance(print_msg, bool)), error_message("Erroneous Type", "check_prior_extract")        
        
        folder_messages = create_messages("Folder ./data")
        json_messages = create_messages("File derpibooru_metadata.json")
        json_path = os.getcwd() + "\\data\\derpibooru_metadata.json"
        
        # Checks if json exists
        if os.path.exists(json_path):
            if print_msg: print(json_messages["found"])
        else:
            # If json doesn't exist, checks if folder ./data exists
            # If folder doesn't exist, creates it
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
            :param <counter>: int ; counter number
            :param <error>: str ; error message
            """
            if back_off_counter > 50: 
                log.error(error)
                raise
            print(f"The program will back off for {2**back_off_counter} seconds.")
            counter += 1
            time.sleep(2 ** counter)
            return counter
        
        derpibooru_url = "https://derpibooru.org/images.json?constraint=id&order=a&gt="
        iterations = self.instances
        back_off_counter = 0
        
        # Checks for prior extracts
        try: json_path = self.check_prior_extract()
        except (IOError, WindowsError) as error:
            log.error(error_message("IO or Windows", "crawl_metadata"))
            raise
        
        with open(json_path, "r") as file: requested_id = json.load(file)
        json_local = requested_id
        if requested_id == []: requested_id = 1
        else: requested_id = requested_id[0]["id"] + 1

        while True:
            try:
                #time delay to respect the API's license
                time.sleep(.200)
                #checks iteration number
                if type(iterations)==int:
                    if iterations > 0: iterations -= 1
                    else: 
                        print(f"{self.instances} images retrieved as requested.")
                        break
                #checks existing data folder and target metadata file
                json_path = self.check_prior_extract(False)
                #requests new derpibooru page
                print(f"You are requesting the derpibooru page starting with the id° {requested_id}.")
                path_derpibooru = derpibooru_url + str(requested_id)
                json_derpibooru = requests.get(path_derpibooru).json()["images"]
                #raise of exception if derpibooru was fully scraped
                if json_derpibooru == []: raise DatabaseFullyCrawled
                #update content of metadata file
                requested_id, json_local = self.json_collect(json_derpibooru, json_local, json_path) 
            except DatabaseFullyCrawled:
                print("The crawler scraped the derpibooru metadata. The program will now close.")
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
            # Deletes unwanted keys
            for item in image_data: 
                if item not in stored_keys: del temp[item]
            last_id = max(image_data["id"], last_id)
            json_local.append(temp)
            json_local.sort(key=operator.itemgetter("id"), reverse = True)
        # Saves the json
        with open(json_path,'w') as file: json.dump(json_local, file)
        
        # Tests if json splitting is necessary
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
        :param <tags>: <list> ; list of strings (i.e. picture tags)
        :param <at_least_one>: <boolean> ; toggles 'at least one tag' option instead of 'all tags'
        """
        def any_or_all(boolean):
            """
            Returns the function any() if argument <boolean> TRUE, else returns function all()
            ---
            :param <boolean>: <boolean> ; boolean value
            """
            if boolean == True: return any
            else: return all
        
        metadata_files_list = filter(lambda file: file.startswith("derpibooru_metadata"), 
                                     os.listdir(os.getcwd() + "\\data"))
        metadata_files_list = list(metadata_files_list)
        id_list = []
        url_list = []
        
        for fname in metadata_files_list:
            try:
                with open(os.getcwd() + "\\data\\" + fname,"r") as file: json_local = json.load(file)
                if json_local == []: break
                tags_keep = list(filter(lambda item: item.startswith("+"), tags))
                tags_keep = list(map(lambda item: item[1:], tags_keep))
                tags_remove = list(filter(lambda item: item.startswith("-"), tags))
                tags_remove = list(map(lambda item: item[1:], tags_remove))
                fltr = any_or_all(at_least_one)
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
        ---
        :param <self>: <class> ; class object reference
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
                    log.error(io_windows_error)
                    raise
                except (requests.exceptions.TooManyRedirects, requests.exceptions.RequestException) as error:
                    log.error(f"REQUEST ERROR: {error}.")
                    raise
                except requests.exceptions.HTTPError as error:
                    log.error(f"REQUEST [HTTP] ERROR: {error}.")
                    raise
                except requests.exceptions.ConnectionError as error:
                    log.error(f"REQUEST [CONNECTION] ERROR: {error}.")
                    raise
                except requests.exceptions.Timeout as error:
                    log.error(f"REQUEST [TIMEOUT] ERROR: {error}.")
                    raise
            try:
                with open(os.getcwd() + "\\data\\" + fname,'w') as file: json.dump(json_local, file)
            except (IOError, WindowsError) as error:
                log.error(io_windows_error)
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