import json
import operator
import os
import numpy as np
import random
import requests
import time

class img_metadata:
    """
    Class object that describes the process on how to retrieve picture metadata from derpibooru's
	REST API. Data is retrieved as a series of c. 1Mb JSON files.
    """
    def __init__(self, tags = [], at_least_one = True, instances = 10):
        """
        Initializes of the img_metadata class object.
        ---
        :param <self>: <class> ; class object reference
        :param <tags>: <list> ; list of strings (i.e. picture tags)
        :param <at_least_one>: <boolean> ; toggles 'at least one tag' option instead of 'all tags'
        :param <instances>: <integer> ; number of instances/loops allowed before stop
        """
        try:
            assert isinstance(tags, list)
            assert isinstance(instances, int)
            assert isinstance(at_least_one, bool)
        except AssertionError as a:
            print("An assertion error was raised at initiation of the class img_metadata located in " + \
			"the derpi_get/core_class.py file.", a, sep = "\n")
			
        self.tags = tags
        self.at_least_one = at_least_one
        self.instances = instances
    
    def bytes_length(self, bytes_size):
        """
        Calculates approximate byte length of a file, based on the assumption that the file will
		not exceed 1,000Tb in size.
        ---
        :param <self>: <class> ; class object reference
        :param <bytes_size>: <integer> ; size in bytes of a file
        """
        try:
            assert isinstance(bytes_size, int)
        except AssertionError as a:
            print("An assertion error was raised while using the method bytes_length() within the " + \
			"class img_metadata located in the derpi_get/core_class.py file.", a, sep = "\n")
        
        for unit_multiple in ['bytes', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return "%3.1f %s" % (bytes_size, unit_multiple)
            bytes_size /= 1024.0
    
    def keys_to_keep(self):
        """
        Returns the keys to keep in the JSON extract.
        keys available:
        {"id", "created_at", "updated_at", "first_seen_at", "tags", "tag_ids", "uploader_id",
        "score", "comment_count", "width", "height", "tag_count", "file_name", "description",
        "uploader", "image", "upvotes", "downvotes", "faves", "aspect_ratio", "original_format",
        "mime_type", "sha512_hash", "orig_sha512_hash", "source_url", 
        "representations":{
            "thumb_tiny", "thumb_small", "thumb", "small", "medium", 
            "large", "tall", "full", "webm", "mp4"},
        "is_rendered", "is_optimized", "interactions", "spoilered"}
        ---
        :param <self>: <class> ; class object reference
        """
        keys_to_keep = ["id", "created_at", "updated_at", "score", "uploader",
                        "uploader_id", "upvotes", "downvotes", "faves", "tags",
                        "tags_id", "aspect_ratio", "representations"]
        return keys_to_keep
    
    def json_archive(self, path):
        """
        Splits a json file if it is too large (1Mb).
        ---
        :param <self>: <class> ; class object reference
        :param <path>: <string> ; path of a json file to weigh
        """
        try:
            assert isinstance(path, str)
        except AssertionError as a:
            print("An assertion error was raised while using the method json_archive() within the " + \
			"class img_metadata located in the derpi_get/core_class.py file.", a, sep = "\n")
			
        length = self.bytes_length(float(os.stat(path).st_size))
        length = length.split(" ") #checks the size of file of path <path>
		
        if float(length[0]) >= 1.0 and length[1] == "MB":
            nb_file = -1
            while True:
                nb_file += 1
                new_path = path[:-5] + "_" + str(nb_file) + ".json"
                if os.path.exists(new_path) == False:
                    print("JSON MAX FILE SIZE REACHED: JSON file to be archived and a new one created.")
                    try:
                        os.rename(path, new_path)
                    except (IOError, WindowsError) as a:
                        print("An assertion error was raised while using the method json_archive() within the " + \
						"class img_metadata located in the derpi_get/core_class.py file.", a, sep = "\n")
                    break
					
    def check_prior_extract(self, print_msg = True):
        """
        Checks if prior JSON extractions exist in the working directory (possibly created by self.json_archive()
        The default file name is 'derpibooru_metadata.json'.
        ---
        :param <self>: <class> ; class object reference
        :param <print_msg>: <boolean> ; toggle between 'prints message to command line' and 'prints nothing'
        """
        try:
            assert isinstance(print_msg, bool)
        except AssertionError as a:
            print("An assertion error was raised while using the method check_prior_extract() within the " + \
			"class img_metadata located in the derpi_get/core_class.py file.", a, sep = "\n")
		
        json_found = "FILE FOUND: 'derpibooru_metadata.json'"
        json_not_found = "FILE MISSING: 'derpibooru_metadata.json'; NOT IN: folder 'data'\n" + \
                        "FILE TO CREATE: 'derpibooru_metadata.json'"
        json_created = "FILE CREATED: 'derpibooru_metadata.json'"
        json_not_created = "FILE CREATION ERROR: 'derpibooru_metadata.json' not created"
        json_path = os.getcwd() + "\\data\\derpibooru_metadata.json"
        
        no_existing_folder = "FOLDER MISSING: Folder 'data' not found\n" + \
							"FOLDER TO CREATE: 'data' to be created in working directory."
        folder_created = "FOLDER CREATED: New folder 'data' created in working directory."
        folder_not_created = "FOLDER CREATION ERROR: Folder 'data' not created in working directory."
        find = os.path.exists(json_path)
        
        #if TRUE: opens file and extracts the contained metadata
        #if FALSE: creates file storing an empty list
        if find and print_msg: print(json_found)
        if not print_msg and print_msg: print(json_not_found)
        
        if not os.path.exists(os.getcwd() + "\\data"):
            try:
                print(no_existing_folder)
                os.makedirs(os.getcwd() + "\\data")
                with open(json_path, "w") as file: file.write("[]") 
                print(folder_created)
            except (IOError, WindowsError) as a:
                print(folder_not_created)
                print("An assertion error was raised while using the method check_prior_extract() " + \
				"within the class img_metadata located in the derpi_get/core_class.py file.", a, sep = "\n")
        print(json_created)
        return json_path

    def crawl_metadata(self):
        """
        Retrieves from the derpibooru REST API a list of picture metadata.
        ---
        :param <self>: <class> ; class object reference
        """
        #initializes local variables    
        iterations = self.instances
        back_off_counter = 1
        max_instances_reached = "The set maximum number of images to request was reached " + \
                                f"at {self.instances}."
        exit_condition = "The crawler scraped the derpibooru metadata. The program will " + \
                         "now close."
        
        #retrieves most recent recorded picture id
        if os.path.exists(os.getcwd() + "\\data\\derpibooru_metadata.json"): 
            json_path = os.getcwd() + "\\data\\derpibooru_metadata.json"
        else: 
            json_path = self.check_prior_extract()
        
        with open(json_path, "r") as file: requested_id = json.load(file)
        
        if requested_id == []: requested_id = 1
        else: requested_id = requested_id[0]["id"] + 1
        
        while True:
            requested_page = "You are requesting the derpibooru page starting with the " + \
                             f"id {requested_id}."
            error_json_extraction = "The program couldn't extract the page and " + \
                                    "will now proceed to an exponential back off."
            
            #checks if previous JSON was not renamed due to the 1Mb splitting
            json_path = self.check_prior_extract(False)
            
            with open(json_path,'r') as file: json_local = json.load(file)
            
            print(requested_page)
            
            path_derpibooru = "https://derpibooru.org/images.json?constraint=id&order=a&gt=" + \
                              str(requested_id)
            
            try:
                if type(iterations) == int:
                    if iterations > 1: iterations -= 1
                    else: break
                
                json_derpibooru = requests.get(path_derpibooru).json()["images"]
                if json_derpibooru == []: raise DatabaseFullyCrawled
                
                requested_id = self.json_collect(json_local, json_derpibooru, json_path)
                
                #time delay to respect the API's license
                time.sleep(.200)
            
            except DatabaseFullyCrawled:
                print(exit_condition)
                break
            
            except Exception as e:
                print(e)
                print(error_json_extraction)
                print(f"The error was the following: {e}.\n The program will back " + \
                      f"off for {2**back_off_counter} seconds.")
                back_off_counter += 1
                time.sleep(2 ** back_off_counter)

    def json_collect(self, json_local, json_derpibooru, json_path):
        """
        Stores a json file for later use with a specific numbered name when its size reaches
		1Mb. Storing is performed by renaming the target file.
        ---
        :param <self>:            <class>       ; class object reference
        :param <json_local>:      <json_object> ; JSON data stored locally
        :param <json_derpibooru>: <json_object> ; JSON data extracted from derpibooru
        :param <json_path>:       <string>      ; path of local file where the data is stored
        """
        stored_keys = self.keys_to_keep()
        last_id = -1
        
        for image_data in json_derpibooru:
            
            temp = image_data.copy()
            
            for item in image_data: 
                if item not in stored_keys: del temp[item]
            
            last_id = max(image_data["id"], last_id)
            
            json_local.append(temp)
            json_local.sort(key=operator.itemgetter("id"), reverse = True)

        with open(json_path,'w') as file: json.dump(json_local, file)
        
        self.json_archive(json_path)
        
        return last_id
    
    def id_filter(self, tags, at_least_one):
        """
        Retrieves the IDs of the locally stored metadata that fit specific tag parameters
        ---
        :param <self>:             <class>   ; class object reference
        :param <tags>:             <list>    ; list of strings (i.e. picture tags)
        :param <at_least_one>:     <boolean> ; toggles 'at least one tag' option instead of 'all tags'
        """
        def any_or_all(boolean):
            """
            Returns the function any() if argument <boolean> TRUE, else returns function all()
            ---
            :param <boolean>: <boolean> ; boolean value
            """
            if boolean == True:
                return any
            else:
                return all
        
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
                filter_url = lambda item: item["representations"]["large"][2:]
                id_list += list(map(filter_id, json_kept))
                url_list += list(map(filter_url, json_kept))
            except Exception as e:
                print(f"There was an error during the JSON load of file {fname}:\n{e}")
        
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
                    if json_local == []:break
                    
                    for index, item in enumerate(json_local):
                        
                        if item["tags"] == None:
                            json_id = item["id"]
                            path_derpibooru = "https://derpibooru.org/" + str(json_id) + ".json"
                            
                            try:
                                json_derpibooru = requests.get(path_derpibooru).json()
                                time.sleep(.250)
                                if json_derpibooru["tags"] == None: raise AbsentTagList
                                json_local[index]["tags"] = json_derpibooru["tags"]
                                print(f"The tags of the picture {json_id} were updated.")
                                
                            except AbsentTagList:
                                print(f"The url request for the picture {json_id} returned an empty list of tags.")
                                
                            except Exception as e:
                                print(e)
                except Exception as e:
                    print(f"There was an error during the JSON load of file {fname}:\n{e}")
                    
            with open(os.getcwd() + "\\data\\" + fname,'w') as file: json.dump(json_local, file)

class Error(Exception):
    """Base class for other exceptions"""
    pass

class DatabaseFullyCrawled(Error):
    """Raised when the crawler reached the last pages of derpibooru"""
    pass

class NewContentCrawled(Error):
    """Raised when the input value is too large"""
    pass

class AbsentTagList(Error):
    """Raised when the key value of the key 'tags' in a dictionary is 'None'"""
    pass