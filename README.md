# derpi_get
derpi_get is a module built to retrieve derpibooru.org (abbrev. derpi) metadata and pictures. Users can leverage two functionalities:
- download of derpi metadata (as a series of 1Mb .json files)
- download of derpi pictures, based on a list of IDs that can be built using the first functionality

### Installation
derpi_get requires Python 3.x. It has the following dependencies:
>  json, operator, os, numpy, random, requests, time

### Available functions
| method | description | variables |
| ------ | ------ | ------ |
| derpibooru_search() | Initializes your scraper object using this function | self |
| change_search() | Changes the arguments of the created object derpibooru_search | self, tags, at_least_one, instances |
| crawl() | launches the scraping of derpi's picture metadata | self |
| retrieve_ids() | Retrieves the IDs of the locally stored metadata that fit specific tag parameters | self |
| repair() | Repairs missing tags of the locally stored metadata | self |
| request_imgs() | Retrieves a number of images from derpibooru based on a list of IDs that can be built using retrieve_ids() | self, tags, id_list, nb_of_requests |
##### Listed variables
| variable name | description | type | initialized at |
| ------ | ------ | ------ | ------ |
| tags | List of strings (e.g. ["tag1", "tag2"]) | List | [] |
| at_least_one | Toggles 'at least one tag' option instead of 'all tags' during the use of retrieve_ids() | Boolean | True |
| instances | Number of instances/loops allowed before program stops | Integer | 10 |
| id_list | List of strings (i.e. picture id + url) built from retrieve_ids() | List | N/A |
| nb_of_requests | Number of images to request for the use of request_mgs() | Integer | None |
> Individual tags must be preceded by a symbol + or - such as "+tag1". The + symbol includes, the - symbol excludes. 

> The variable "at_least_one" specifies whether the id search retrieve ids with at least one of the tags flagged with a "+" or if the search retrieve only the ids that have all the tags flagged with a "+" 

### Code of conduct and TOS
Anyone can use the following module. However, respect the Derpibooru licensing rules. Users making abusively high numbers of requests may be asked to stop by the website administrators. Your application **must** properly cache, and respect server-side cache expiry times. Your client **must** gracefully back off if requests fail (eg non-200 HTTP code), preferably exponentially or fatally.
As-is, the module puts time caps between each request to the derpibooru server: 
- 0.2s between two metadata requests
- 0.5s between two image requests
### License
MIT