import git
import os
import datetime
from datetime import datetime, timedelta
import shutil
import os
from termcolor import colored
from pprint import pprint
import logging
import json
from lib_openAPI import queryOpenAPI
import textwrap

# SigmaHQPullHistry:
#   - main utility class for this script. pulls the sigmaHQ repo then looks at the commit history
#     saves data in a json file.
#     if there is an openAPI key provided, it uses openAI/chatGPT to summarize the sigma code
class sigmaHQPullHistory:
    def __init__(self, config, repo_folder, repo_url, logger):
        self.config = config
        self.logger = logger
        self.repo_folder = repo_folder
        self.repo_url = repo_url
        self.fileDataStore=self.readDataStoreFromFile(file_path='./dataStore.json')
        self.openAPI_obj=queryOpenAPI(config=config, logger=logger)

        logger.info (f'class object created for sigmaHQHistoryPull')
        self.repo_folder = repo_folder

    #queryRepo: pulls commit history for a certain number of days from repo's master branch
    def queryRepo(self, days):
        # Replace with the branch name
        branch_name = 'master'

        self.delete_folder(self.config['download_folder'])
        # Clone the repository to a local directory
        repo = git.Repo.clone_from(self.repo_url, self.repo_folder)

        # Get the commits
        self.commits = list(repo.iter_commits(f'origin/{branch_name}', since=datetime.now() - timedelta(days=days)))
        logging.info(f'repo updated, commits read..')

    # processRepo: parses/processes commit history pulled from repo commit history
    def processRepo(self):
        print (f'- Processing repo History:')
        for commit in self.commits:
            selectedColor=self.setColor(commit.summary)
            print (colored(f'  [+]: {commit.summary}', selectedColor))
            fileList=self.getFileList(commit)

            for file in fileList:
                if ".yml" in file:
                    print (colored(f'     [+]: {file}', selectedColor))
                    self.addToDataStore(file, pushComment=commit.summary)
        print (f'  ')

    # addToDataStore: adds commit history data to a python dictionary, if openAPI key is added, file summary
    #                 created by chatgpt/openAI
    def addToDataStore(self, filename, pushComment):
        if ".yml" in filename:
            tempEntry = {
                        'filename': filename,
                        'creation_Date': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f'),
                        'modification_Date': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f'),
                        'lastUpdate_Date': 0,
                        'sigmaRule': self.readFile(filename),
                        "summary": "",
                        "modification_count": 1,
                        "comment_history": []
            }

            if self.fileDataStore.get(filename):  # in db
                self.fileDataStore[filename]['comment_history'].append(pushComment)
                self.fileDataStore[filename]['comment_history'] = list(set(self.fileDataStore[filename]['comment_history']))
                self.fileDataStore[filename]['modification_count'] += 1
                self.fileDataStore[filename]['modification_Date'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
                self.fileDataStore[filename]['lastUpdate_Date'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')

            else:  # new db entry
                if "<put" not in self.config['openAI_API_Key']: #if there is a real API key in config file
                    tempEntry['summary'] = str(self.openAPI_obj.summarizeSigmaRule( tempEntry['sigmaRule']))
                else:
                    print (f'skipping openAPI calls, no API key entered, please check the config.yml')
                tempEntry['lastUpdate_Date'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
                tempEntry['comment_history'].append(pushComment)
                self.fileDataStore[filename] = tempEntry.copy()
                tempEntry.clear()

        else:
            print(f'   [-]: skipping {filename} because it is not a .yml file')

    #getFileList: returns a list of files modified in the commit
    def getFileList(self, commit):
        fileList=commit.stats.files.keys()
        return fileList

    #delete_folder: deletes temp download repo folder
    def delete_folder(self, folder_path):
        try:
            # Delete the folder and its contents
            shutil.rmtree(folder_path)
            self.logger.info(f"Successfully deleted folder: {folder_path}")
        except OSError as e:
            self.logger.debug(f"Error: {folder_path} : {e.strerror}")

    # readFile: reads sigma file
    def readFile(self, filename):
        fileWithRepo=self.repo_folder+"/"+filename
        self.logger.info(f'   [+]:  {fileWithRepo}')

        if os.path.exists(fileWithRepo):
            with open(fileWithRepo, 'r') as file:
                # Read the entire contents of the file
                content = file.read()
            return content

        else:
            return "file does not exist"

    # showDataStore: displays data to terminal screen
    def showDataStore(self):
        for item in self.fileDataStore:
            data=self.fileDataStore.get(item)

            colorChoice=self.setColor(data['comment_history'][0])

            print(colored(f'--=========================================--', colorChoice))
            print(colored(f'  {data['comment_history'][0]}', colorChoice))
            print(colored(f'--=========================================--', colorChoice))
            print(colored(f'Date: {data.get('modification_Date')}', colorChoice))
            print(colored(f'Filename: {data.get('filename')}', colorChoice))

            wrapped_text = textwrap.fill(("Summary: " + data.get('summary')), width=150)
            print(colored(f'{wrapped_text}', colorChoice))
            print (f'     ')

    #saves python data dictionary to JSON file
    def saveDataStore(self):
        data=self.fileDataStore
        file_path='./dataStore.json'
        try:
            # Open and write to the JSON file
            with open(file_path, 'w') as file:
                json.dump(self.fileDataStore, file, indent=4)

            self.logger.debug(f"   [*]: Data successfully written to {file_path}.")

        except Exception as e:
            self.logger.info(f"An error occurred: {e}")
            self.logger.info(f"[-]: An error occurred: {e}")

    # check for file
    def check_file_exists(self, file_path):
        # Check if the file exists
        if not os.path.exists(file_path):
            # Create the file
            with open(file_path, 'w') as file:
                # Optionally write initial content to the file
                file.write('{}')
            self.logger.debug(f"   [+]: DataStore {file_path} created.")
        else:
            self.logger.debug(f"   [+]: DataStore {file_path} already exists.")

    #converts text timestamp to python datetime
    def convertStrTimeStamptoDateTime(self, strTimeStamp):
        datetime_obj = datetime.fromisoformat(strTimeStamp)

        # Format the datetime object to the desired format
        # For example, converting to 'YYYY-MM-DD HH:MM:SS' format
        formatted_timestamp = datetime.strptime(strTimeStamp, '%Y-%m-%dT%H:%M:%S.%f')

        return formatted_timestamp

    # reads json data store to python dictionary
    def readDataStoreFromFile(self, file_path):
        file_path=file_path
        self.check_file_exists(file_path)

        try:
            # Open and read the JSON file
            with open(file_path, 'r') as file:
                data = json.load(file)
                self.logger.debug("   [+]: reading data from file.")
                self.dataStore=data.copy()

            return data
        except FileNotFoundError:
            self.logger.debug("[+]: The file does not exist.")
        except json.JSONDecodeError as e:
            self.logger.debug(f"[-]: Invalid JSON in file: {file_path}. Error: {e}")
        except Exception as e:
            self.logger.debug(f"[-]: An error occurred: {e}")
        return None

    def setColor(self, comment):
        redList=self.config['redList']
        yellowList=self.config['yellowList']
        greenList=self.config['greenList']

        for word in redList:
            # Check if the word is in the text
            if word.lower() in comment.lower():
                return "red"

        for word in yellowList:
            # Check if the word is in the text
            if word.lower() in comment.lower():
                return "yellow"

        for word in greenList:
            # Check if the word is in the text
            if word.lower() in comment.lower():
                return "green"
        return "blue"

