import requests

class ApiLoader:
    def __init__(self,IP, PORT):
        self.ADR = f'{IP}:{PORT}'

    def loadFolderList(self, user_name):
        response = requests.get(f"http://{self.ADR}/folder/{user_name}")
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return response.status_code
