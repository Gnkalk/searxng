# Importing necessary libraries
import git
import os
import shutil
import json

# Function to delete cache in a given folder
def delete_cache_in_folder(folder_path):
    file_list = os.listdir(folder_path)  # List all files in the folder
    for file_name in file_list:  # For each file in the folder
        file_path = os.path.join(folder_path, file_name)  # Get the full path of the file
        if os.path.isfile(file_path):  # If it's a file
            os.remove(file_path)  # Remove the file
        elif os.path.isdir(file_path):  # If it's a directory
            delete_cache_in_folder(file_path)  # Recursively delete cache in the directory

# Function to delete cache in the 'mpm_cache' folder
def delete_folder_cache():
    cache_folder = 'mpm_cache'
    delete_cache_in_folder(cache_folder)

# Function to check a file and extract its type
def check_file_and_extract_type(name):
    file_path = os.path.join(f"mpm_cache/{name}", "Information.json")  # Path to the Information.json file

    if not os.path.exists(file_path):  # If the file does not exist
        print("Error: The Information.json file was not found")  # Print an error message
        return

    with open(file_path, "r") as file:  # Open the file
        data = json.load(file)  # Load the JSON data from the file
        file_type = data.get("type")  # Get the 'type' field from the data

        if file_type:  # If the 'type' field exists
            return file_type  # Return the 'type'
        else:  # If the 'type' field does not exist
            print("Error: The Information.json file is corrupted")  # Print an error message

# Function to extract the repository name from a URL
def extract_repository_name(url):
    url_parts = url.split("/")  # Split the URL into parts
    repository_name = url_parts[-1]  # Get the last part of the URL
    repository_name = repository_name.split(".")[0]  # Remove the file extension
    return repository_name  # Return the repository name

# Function to clone a repository
def clone_repository(url):
    git.Repo.clone_from(url, "mpm_cache")  # Clone the repository into the 'mpm_cache' folder

# Function to install a package
def instaler(p_type, name):

    if p_type == "engine":  # If the package is an engine
        destination_file = os.path.join("/searx/engines/", file)  # Destination for the file
        files = os.listdir(f"/mpm_cache/{name}")  # List all files in the 'mpm_cache' folder

        for file in files:  # For each file
            source_file = os.path.join(f"/mpm_cache/{name}", file)  # Get the full path of the file
            shutil.move(source_file, destination_file)  # Move the file to the destination

    elif p_type == "answerer":  # If the package is an answerer
        destination_file = os.path.join("/searx/answerers/", file)  # Destination for the file
        files = os.listdir("/mpm_cache")  # List all files in the 'mpm_cache' folder

        for file in files:  # For each file
            source_file = os.path.join("/mpm_cache", file)  # Get the full path of the file
            shutil.move(source_file, destination_file)  # Move the file to the destination

    elif p_type == "plugin":  # If the package is a plugin
        destination_file = os.path.join("/searx/plugins/", file)  # Destination for the file
        files = os.listdir("/mpm_cache")  # List all files in the 'mpm_cache' folder

        for file in files:  # For each file
            source_file = os.path.join("/mpm_cache", file)  # Get the full path of the file
            shutil.move(source_file, destination_file)  # Move the file to the destination
    elif p_type == "theme":  # If the package is a theme
        destination_file = os.path.join("/searx/static/", file)  # Destination for the file
        files = os.listdir("/mpm_cache/static")  # List all files in the 'mpm_cache/static' folder

        destination_file_templates = os.path.join("/searx/static/", file)  # Destination for the templates
        files_templates = os.listdir("/mpm_cache/static")  # List all files in the 'mpm_cache/static' folder

        for file in files:  # For each file
            source_file = os.path.join("/mpm_cache", file)  # Get the full path of the file
            shutil.move(source_file, destination_file)  # Move the file to the destination
        for file in files_templates:  # For each template
            source_file = os.path.join("/mpm_cache", file)  # Get the full path of the file
            shutil.move(source_file, destination_file_templates)  # Move the file to the destination

# Function to list all installed packages
def lister():
    current_directory = os.path.dirname(os.path.abspath(__file__))  # Get the current directory

    # print engines
    contents = os.listdir(current_directory + "/searx/engines/")  # List all files in the 'searx/engines' folder
    filtered_items = [item for item in contents if item != "__init__.py" and not item.endswith("pycache")]  # Filter out unwanted files
    engines = ""  # Initialize the list of engines
    for item in contents:  # For each file
        if item == "__init__.py" or item.endswith("__pycache__"):  # If the file is not wanted
            continue  # Skip the file
        else:
            engines += item + "  "  # Add the file to the list of engines

    # print answerers
    contents = os.listdir(current_directory + "/searx/answerers/")  # List all files in the 'searx/answerers' folder
    answerers = ""  # Initialize the list of answerers
    for item in contents:  # For each file
        if item == "__init__.py" or item.endswith("__pycache__"):  # If the file is not wanted
            continue  # Skip the file
        answerers += item + ", "  # Add the file to the list of answerers

    # print plugins
    contents = os.listdir(current_directory + "/searx/plugins/")  # List all files in the 'searx/plugins' folder
    plugins = ""  # Initialize the list of plugins
    for item in contents:  # For each file
        if item == "__init__.py" or item.endswith("__pycache__"):  # If the file is not wanted
            continue  # Skip the file
        plugins += item + ", "  # Add the file to the list of plugins

        # print themes
    contents = os.listdir(current_directory + "/searx/static/themes/")  # List all files in the 'searx/static/themes' folder
    themes = ""  # Initialize the list of themes
    for item in contents:  # For each file
        themes += item + ", "  # Add the file to the list of themes

    ret = f'''
engines:
{engines}

answerers:
{answerers}

plugins:
{plugins}

themes:
{themes}

    '''
    return ret

text = ''' mpm MOA package manager
To install the package:
install <git url>

To remove the package:
remove <package name>

For the list of packages:
list
'''
print(text)

while True:
    delete_folder_cache()
    command = input(">>>")
    words = command.split()
    first_word = words[0] if words else ""

    if first_word in ("install", "i"):
        if len(words) >= 2:
            second_word = words[1]
            pack_name = clone_repository(second_word)
            pack_type = check_file_and_extract_type(pack_name)
            if pack_type:
                installer(pack_type, pack_name)
            else:
                continue
        else:
            print("Package name is missing.")
            continue

    elif first_word in ("remove", "r"):
        print("test")
    elif first_word in ("list", "l"):
        print(lister())
    elif first_word == "exit":
        break
    else:
        print("No such command found")
