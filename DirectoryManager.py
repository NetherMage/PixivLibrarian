import os

class Directory:
    def __init__(self, abs_path, rel_path):
        self.abs_path = os.path.abspath(abs_path)
        self.rel_path = rel_path
        self.dir_name = abs_path.split('\\')[-1]
        
    def __repr__(self):
        return f"Directory(abs_path='{self.abs_path}', rel_path='{self.rel_path}', dir_name='{self.dir_name}')"

class DirectoryManager:
    def __init__(self, root_path):
        self.root_path = os.path.abspath(root_path)
        self.directories = []
        self._crawl_directory(self.root_path, "")
        
    # Crawl all directories in root_path and populate the self.directories list for future usage
    def _crawl_directory(self, current_path, rel_path):
        for entry in os.scandir(current_path):
            if entry.is_dir():
                abs_path = entry.path
                new_rel_path = os.path.join(rel_path, entry.name)
                directory = Directory(abs_path, new_rel_path)
                self.directories.append(directory)
                self._crawl_directory(abs_path, new_rel_path)

    # Get a list of all directories in format of Dir(abs_path, rel_path, dir_name)
    def get_directories(self):
        return self.directories