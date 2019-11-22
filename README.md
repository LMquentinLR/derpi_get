# derpi_get
derpi_get is a module built to retrieve derpibooru.org (abbrev. derpi)^picture metadata and related pictures. Users can leverage two download functionalities:
- download of derpi metadata (as a series of 1Mb .json files)
- download of derpi pictures, based on a list of IDs that can be constructed based on the data retrieved with the first functionality

### Installation
derpi_get requires Python 3.x. It has the following dependencies:
>  json, operator, os, numpy, random, requests, time

### Available functions
| method | description | arguments/attributes/variables |
| ------ | ------ | ------ |
| derpibooru_search() | [Class] Initialize your scraper object using this function | self |
| change_search() | [Method] Changes the arguments of the derpibooru_search object | self, tags, at_least_one, instances |
| crawl() | [Method] Scraps derpi picture metadata frm the most recent to the oldest item | self |
| retrieve_ids() | [Method] Constructs an ID list based on the locally stored metadata, fitting specific tag parameters provided by the user through initialization or change_search() | self |
| repair() | [Method] Checks for broken/missing tags of the locally stored metadata and completes/repairs them | self |
| request_imgs() | [Method] Requests the images from the derpi websited based on a list of IDs that can be built using retrieve_ids() | self, tags, id_list, nb_of_requests |

##### Listed variables
| variable name | description | type | initialized as |
| ------ | ------ | ------ | ------ |
| tags | List of strings (e.g. ["tag1", "tag2"]) | List | [] |
| at_least_one | Toggles 'at least one tag' option: IDs are kept if they list at least one tag stored as a string in tags during the use of retrieve_ids(). If False, 'all tags' is toggled and only pictures with all of the listed tags will be kept during the use of retrieve_ids() | Boolean | True |
| instances | Number of instances/loops allowed before program stops. A loop will usually requests 50 pictures | Integer | 10 |
| id_list | List of strings (i.e. picture id + url) built from retrieve_ids() | List | N/A |
| nb_of_requests | Number of images to request during the running of request_img() | Integer | None |

**important notes**

> In the variable list "tags", individual tag string must be preceded by a symbol + or - such as "+tag". The + symbol indicates that, to be retrieved, a picture must have at least that tag (depending on the at_least_one argument). The - symbol indicates that the picture will never be retrieved, even if it has tags flagged with a +. 

> I.e. The variable "at_least_one" specifies whether the id search retrieve ids with at least one of the tags flagged with a "+" or if the search retrieve only the ids that have all the tags flagged with a "+".

### Code of conduct and TOS
Anyone can use the following module. However, respect the Derpibooru licensing rules. Users making abusively high numbers of requests may be asked to stop by the website administrators. Your application **must** properly cache, and respect server-side cache expiry times. Your client **must** gracefully back off if requests fail (eg non-200 HTTP code), preferably exponentially or fatally.
As-is, the module puts time caps between each request to the derpibooru server: 
- 0.2s between two metadata requests
- 0.2s between two image requests

### License
MIT