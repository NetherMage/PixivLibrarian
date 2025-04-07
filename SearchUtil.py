from fuzzysearch import find_near_matches
from Levenshtein import distance
import enchant

from DirectoryManager import DirectoryManager

class SearchUtil:
    def __init__(self, root_path):
        self.dir_mngr = DirectoryManager(root_path)

    # unused
    def search(self, pattern, searchCount):
        pattern = pattern.strip().upper()
        result_list = self.fuzzysearch(pattern)
        result_list.sort(key=lambda x: (enchant.utils.levenshtein(x['matched'].upper(), pattern) * -100) + enchant.utils.levenshtein(x['string'].upper(), pattern), reverse=True)
        return result_list[:searchCount]

    def search_dir(self, pattern):
        #TODO
        # Get directories as all_list from DirectoryManager - DONE
        # Call fuzzysearch on user input 'text' and dictionary's dirName list. - DONE
        # Expects to receives more than 1 result as it is fuzzy search. - DONE
        # Create another result_list that is a list of dictionary that maps the result against all_list. - DONE
        dir_list = self.dir_mngr.get_directories()
        
        # Perform fuzzy search based on dictionary list dirName column
        dir_name_list = [item.dir_name for item in dir_list]
        search_result_list = self.fuzzysearch(dir_name_list, pattern)

        # Filter dir_list against search_result_list
        mapped_result_list = [x for item in search_result_list for x in dir_list if x.dir_name == item['matching_string']]

        return(mapped_result_list)

    def fuzzysearch(self, string_list, keyword):
        result_list = []
        keyword_upper = keyword.upper()

        for string in string_list:
            string_upper = string.upper()
            match = find_near_matches(keyword_upper, string_upper, max_l_dist=1)

            if match:
                # Calculate similarity using Levenshtein distance
                edit_distance = distance(keyword_upper, string_upper)

                item = {
                    "matching_string": string,
                    "matched_letters": match[0].matched,
                    "similarity_score": edit_distance
                }
                result_list.append(item)
        
        # Sort the result list by similarity_score (lower score means more similar)
        result_list.sort(key=lambda x: x['similarity_score'])

        return result_list
