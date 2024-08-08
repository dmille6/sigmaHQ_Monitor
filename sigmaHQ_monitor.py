import shutil
import os
import logging
from lib_sigmaHQPullHistory import sigmaHQPullHistory
import yaml

# checks for config.yml, if there is not one, it creates one and exits
def checkForConfig(file_path):
    if os.path.isfile(file_path):
        return True
    else:
        shutil.copyfile('config.yml.example', 'config.yml')
        print (f'ERROR: No configuration file found, created a new one: {file_path}')
        print (f'       Please edit this file, adding your information, then re-run the script')
        return False

#reads config.yml
def read_yaml_config(file_path):
    try:
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)
            return config

    except yaml.YAMLError as e:
        print(f"Error reading YAML file: {e}")
    except FileNotFoundError:
        print("The specified YAML file was not found.")

if __name__ == '__main__':
    print ("\n")
    print("----------------------")
    print("-- Sigma HQ Monitor --")
    print("----------------------")

    #checks for configuration file
    if checkForConfig('./config.yml'):
        config=read_yaml_config('./config.yml')

        # Configure logging settings
        logging.basicConfig(
            level=logging.INFO,  # Set the logging level to DEBUG
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Log message format
            filename='sigmaHQ_Monitor.log',  # Log file name
            filemode='a'  # Append mode
        )

        logger = logging.getLogger('sigmaHQ Logger')
        logger.info(f'--===========================================--')

        # sets github repo info from configuration file
        root_folder = config['download_folder']
        repo_url = config['repo_url']

        print(f"- Pulling Repo: {repo_url} to Folder: {root_folder}")

        logger.info(f'{root_folder} : {repo_url}')
        logger.info(f'--===========================================--')

        sigmahq_obj = sigmaHQPullHistory(config=config, repo_folder=root_folder, repo_url=repo_url, logger=logger)

        # pulls commit history for a certain amount of days set in config.yml
        sigmahq_obj.queryRepo(days=config['days'])
        sigmahq_obj.processRepo()

        print (f'\nDetailed Sigma File Info:')
        sigmahq_obj.showDataStore()
        sigmahq_obj.saveDataStore()

        #deletes/removes temp download folder
        sigmahq_obj.delete_folder(root_folder)