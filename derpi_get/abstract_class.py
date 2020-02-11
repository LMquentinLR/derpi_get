from .core_class import img_metadata
import logging
import os
import random
import requests
import time

log = logging.getLogger()

class derpibooru_search(img_metadata):
    """
    Class object describing a search prompt to the derpibooru REST API.
    Retrieves both picture metadata and  affiliated images.
    """
    
    def change_search(self, tags = [], at_least_one = True, instances = 10):
        """
        Changes the search parameters of the created object derpibooru_search.
        ---
        :param <self>: <class> ; class object reference
        :param <tags>: <list> ; list of strings (i.e. picture tags)
        :param <at_least_one>: <boolean> ; toggles 'at least one tag' option instead of 'all tags'
        :param <instances>: <integer> ; number of instances/loops allowed before stop
        """
        error_msg = "WRONG TYPE: An assertion error was raised while changing the parameters of the class " + \
                    "derpibooru_search() located in the derpi_get/abstract_class.py file."
        if not isinstance(tags, list): raise AssertionError(error_msg + "\n<tags> variable not a 'list'")
        if not isinstance(at_least_one, bool): raise AssertionError(error_msg + "\n<at_least_one> variable not a 'bool'")
        self.tags = tags
        self.at_least_one = at_least_one
        if (isinstance(instances, int) == False) and (instances != ""):
            print("The specified number of <instances> was not recognize. It will be defaulted to 10.")
            self.instances = 10
        else:
            self.instances = instances
            
    def crawl(self):
        """
		Launches the scraping procedure.
		---
		:param <self>: <class> ; class object reference
		"""
        io_windows_error = "IO or WINDOWS ERROR:  An error was raised while using the method crawl() " + \
                           "within the class derpibooru_search located in the derpi_get/abstract_class.py file."
		
        print("----|Entering Derpibooru Data Crawler code|----")
        
        try:
            self.crawl_metadata()
        except DatabaseFullyCrawled:
            print("exit point")
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
        
        print("---------------|Exiting Program|---------------")

    def retrieve_ids(self):
        """
        Retrieves the IDs of locally stored metadata fitting specific tag values.
        ---
        :param <self>: <class> ; class object reference
        """
        error_msg = "WRONG TYPE: An assertion error was raised while while using the retrieve_ids() " + \
                    "within the class derpibooru_search() located in the derpi_get/abstract_class.py file."
        io_windows_error = "IO or WINDOWS ERROR:  An error was raised while using the retrieve_ids() " + \
                           "within the class derpibooru_search located in the derpi_get/abstract_class.py file."

        if not isinstance(self.tags, list): raise AssertionError(error_msg + "\n<tags> variable not a 'list'")
        if not isinstance(self.at_least_one, bool): raise AssertionError(error_msg + "\n<at_least_one> variable not a 'bool'")

        print("----|Retrieving IDs based on tag selection|----")
        try:
            id_list = self.id_filter(self.tags, self.at_least_one)
        except (IOError, WindowsError) as error:
            log.error(io_windows_error)
            raise
        print("----------------|IDs retrieved|----------------")
        return id_list
	
    def repair(self):
        """
		Repairs missing tags of the locally stored metadata.
		---
		:param <self>: <class> ; class object reference
		"""
        io_windows_error = "IO or WINDOWS ERROR:  An error was raised while using the repair() " + \
                           "within the class derpibooru_search located in the derpi_get/abstract_class.py file."
        print("----|Repairing missing tags in stored JSON|----")
        try:
            self.repair_tags()
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
        print("----------------|Tags repaired|----------------")

    def request_imgs(self, tags, id_list, nb_of_requests = None):
        """
		Retrieves images from derpibooru based on a specific ID list.
		---
		:param <self>: <class> ; class object reference
		:param <tags>: <list> ; list of strings (tags used to search ids)
		:param <id_list>: <list> ; list of strings (i.e. picture id + url)
		:param <nb_of_requests>: <integer> ; number of images to request
		"""
        error_msg = "WRONG TYPE: An assertion error was raised while while using the request_imgs() " + \
                    "within the class derpibooru_search() located in the derpi_get/abstract_class.py file."
        io_windows_error = "IO or WINDOWS ERROR:  An error was raised while using the request_imgs() " + \
                           "within the class derpibooru_search located in the derpi_get/abstract_class.py file."
                           
        print("------|Requesting images from derpibooru|-----")

        if not isinstance(tags, list): raise AssertionError(error_msg + "\n<tags> variable not a 'list'")
        if not isinstance(id_list, list): raise AssertionError(error_msg + "\n<id_list> variable not a 'list'")

        try:
            img_path = os.getcwd() + "\\data\\" + "".join(sorted(tags))
            if not os.path.exists(img_path): os.makedirs(img_path)
        except (IOError, WindowsError) as error:
            log.error(io_windows_error)
            raise
            
        if (nb_of_requests == None) or (len(id_list) < nb_of_requests): nb_of_requests = len(id_list)

        length = len(id_list)
        nb_req = 0

        try:
            
            while length > 0:
                random_index = random.randint(0, length - 1)
                item = id_list[random_index]
                id_list.pop(random_index)
                
                nb_req += 1
                length = len(id_list)
                
                image_id = str(item[0])
                path_derpibooru = item[1]
                extension = "." + path_derpibooru.split(".")[-1]
                
                if nb_req > nb_of_requests: 
                    break
                
                picture_path = img_path + "\\" + image_id
                
                if ((os.path.exists(picture_path + ".png")) or
                    (os.path.exists(picture_path + ".jpeg")) or
                    (os.path.exists(picture_path + ".jpg"))): 
                    continue
                
                if not (item[1].endswith("png") 
				or item[1].endswith("jpeg") 
				or item[1].endswith("jpg")):
                    nb_of_requests += 1
                    continue
                
                picture_path += extension
                request = requests.get("http://" + path_derpibooru)
                #print(nb_req, nb_of_requests, picture_path, path_derpibooru)
                if request.status_code == 200:
                    with open(picture_path, 'wb') as f:
                        f.write(request.content)
                time.sleep(.200)
                print(f"The picture {image_id} was downloaded.")
        
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
		
        print("---------------|Images retrieved|--------------")