from .core_class import img_metadata
import os

class derpibooru_search(img_metadata):
    """
    Class object that corresponds to a search prompting the derpibooru REST API and
    retrieve both picture metadata and the affiliated pictures.
    """
    
    def change_search(self, tags = [], at_least_one = True, instances = 10):
        """
        Changes the arguments of the created object derpibooru_search.
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

    def crawl(self):
        """
        Launches the scraping of derpi's picture metadata.
        ---
        :param <self>: <class> ; class object reference
        """
        print("----|Entering Derpibooru Data Crawler code|----")
        self.crawl_metadata()
        print("---------------|Exiting Program|---------------")
    
    def retrieve_ids(self):
        """
        Retrieves the IDs of the locally stored metadata that fit specific tag parameters.
        ---
        :param <self>: <class> ; class object reference
        """
        print("----|Retrieving IDs based on tag selection|----")
        assert isinstance(self.tags, list)
        assert isinstance(self.at_least_one, bool)
		
        id_list = self.id_filter(self.tags, self.at_least_one)
        print("----------------|IDs retrieved|----------------")
        return id_list
    
    def repair(self):
        """
        Repairs missing tags of the locally stored metadata.
        ---
        :param <self>: <class> ; class object reference
        """
        print("----|Repairing missing tags in stored JSON|----")
        self.repair_tags()
        print("----------------|Tags repaired|----------------")

    def request_imgs(self, tags, id_list, nb_of_requests = None):
        """
        Retrieves a number of images from derpibooru.
        ---
        :param <self>:           <class>   ; class object reference
        :param <tags>:           <list>    ; list of strings (tags used to search ids)
        :param <id_list>:        <list>    ; list of strings (i.e. picture id + url)
        :param <nb_of_requests>: <integer> ; number of images to request
        """
        print("------|Requesting images from derpribooru|-----")
        
        assert isinstance(self.tags, list)
        assert isinstance(id_list, list)
        assert isinstance(nb_of_requests, int)
        
        img_path = os.getcwd() + "\\data\\" + "".join(sorted(tags))
        if not os.path.exists(img_path): os.mkdirs(img_path)
        
        for index, item in enumerate(id_list):
            
            image_id = str(item[0])
            path_derpibooru = item[1]
            extension = "." + path_derpibooru.split(".")[-1]
            
            if index > nb_of_requests: 
                break
            
            picture_path = img_path + "\\" + image_id
            if os.path.exists(picture_path + ".png"): 
                continue
            
            if not item[1].endswith(("png")):
                nb_of_requests += 1
                continue

            try:
                picture_path += extension
                request = requests.get("http://" + path_derpibooru)
                if request.status_code == 200:
                    with open(picture_path, 'wb') as f:
                        f.write(request.content)
                
                time.sleep(.5)
                
                print(f"The picture {image_id} was downloaded.")

            except Exception as e:
                print(e)
            
        print("---------------|Images retrieved|--------------")