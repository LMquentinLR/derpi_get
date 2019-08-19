import json
import operator
import os
import numpy as np
import requests
import random
import time

class img_metadata:
    """
    Class object that corresponds to the process retrieving picture metadata from the REST API
    of the website derpibooru--data is retrieved as a series of est. 1Mb JSON files.
    """
    def __init__(self, tags = [], at_least_one = True, instances = 10):
        """
        Initializes of the img_metadata class object.
        ---
        :param <self>:             <class>   ; class object reference
        :param <tags>:             <list>    ; list of strings (i.e. picture tags)
        :param <at_least_one>:     <boolean> ; toggles 'at least one tag' option instead of 'all tags'
        :param <instances>:        <integer> ; number of instances/loops allowed before program stops
        """
        assert isinstance(tags, list)
        assert isinstance(instances, int)
        assert isinstance(at_least_one, bool)
        self.tags = tags
        self.at_least_one = at_least_one
        self.instances = instances
    
    def convert_bytes(self, bytes_size):
        """
        Converts byte lengths.
        ---
        :param <self>:       <class>   ; class object reference
        :param <bytes_size>: <integer> ; size in bytes of a file
        """
        for unit_multiple in ['bytes', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return "%3.1f %s" % (bytes_size, unit_multiple)
            bytes_size /= 1024.0
    
    def keys_to_keep(self):
        """
        Returns the keys to keep in the JSON extract.
        ---
        :param <self>: <class> ; class object reference
        """
        keys = ["id", "created_at", "updated_at", "score", "uploader",
                "uploader_id", "upvotes", "downvotes", "faves", "tags",
                "tags_id", "aspect_ratio", "representations"]
        return keys
    
    def json_split(self, path):
        """
        Splits a json file if it is too large (1Mb).
        ---
        :param <self>: <class>  ; class object reference
        :param <path>: <string> ; path of a json file
        """
        length = self.convert_bytes(float(os.stat(path).st_size))
        length = length.split(" ")
        if float(length[0]) >= 1.0 and length[1] == "MB":
            nb_file = 0
            while True:
                new_path = path[:-5] + "_" + str(nb_file) + ".json"
                if os.path.exists(new_path) == False:
                    print("SPLIT: JSON file to be split as 1Mb max size reached.")
                    os.rename(path, new_path) 
                    break
                nb_file += 1
    
    def check_prior_extract(self, print_msg = True):
        """
        Checks existing metadata extractions in the working directory. 
        The default file name is 'derpibooru_metadata.json'.
        ---
        :param <self>:      <class>   ; class object reference
        :param <print_msg>: <boolean> ; toggle between 'prints message to command line' and 'prints nothing'
        """
        
        json_found = "FOUND: 'derpibooru_metadata.json'"
        json_not_found = "MISSING FILE: 'derpibooru_metadata.json'; NOT IN: folder 'data'\n" + \
                         "FILE TO CREATE: 'derpibooru_metadata.json'"
        json_created = "FILE CREATED: 'derpibooru_metadata.json'"
        json_not_created = "ERROR FILE CREATION: 'derpibooru_metadata.json'"
        json_path = os.getcwd() + "\\data\\derpibooru_metadata.json"
        
        find = os.path.exists(json_path)
        
        #if TRUE: opens file and extracts the contained metadata
        #if FALSE: creates file storing an empty list
        if find:
            if print_msg: print(json_found)
        else:
            if print_msg: print(json_not_found)
            try:
                if not os.path.exists(os.getcwd() + "\\data"): os.makedirs(os.getcwd() + "\\data")
                with open(json_path, "w") as file: file.write("[]")   
                print(json_created) 
            except Exception as e: print(json_not_created, e, sep = "\n")
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
        Collects picture metadata extracted from derpibooru.
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
        
        self.json_split(json_path)
        
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
            
        return list(zip(id_list, url_list))
    
    def repair_tags(self):
        """
        Checks if all retrieved IDs have an available list of tags.
        ---
        :param <self>: <class> ; class object reference
        """
        metadata_files_list = filter(lambda file: file.startswith("derpibooru_metadata"), 
                                     os.listdir(os.getcwd() + "\\data"))
        metadata_files_list = list(metadata_files_list)
        
        for fname in metadata_files_list:
            
            with open(os.getcwd() + "\\data\\" + fname, "r") as file: 
                
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