import base64
import json
import time

import requests


class AccordService:
    def __init__(self, file_location: str = 'configs/accord-config.json'):

        self.results = None
        try:
            with open(file_location) as f:
                data = json.load(f)
        except FileNotFoundError:
            raise Exception("File not found at specified path.")
        self.accordUrl = data['accordUrl']
        self.accordAuthServer = data['accordAuthServer']
        self.accordApiKey = data['accordApiKey']
        self.accordClientId = data['accordClientId']
        self.accordSecret = data['accordSecret']
        self._auth_info = None
        self._sleepSeconds = 5

    def _encodeBasicAuth(self):
        message = f"{self.accordClientId}:{self.accordSecret}"
        message_bytes = message.encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        base64_message = base64_bytes.decode('ascii')
        return base64_message

    def get_auth_token(self):
        ##TODO Add some Cache Logic here
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {self._encodeBasicAuth()}',
            'Accept': '*/*',
            'Cache-Control': 'no-cache'
        }
        data = {
            'grant_type': 'client_credentials'
        }
        response = requests.post(self.accordAuthServer, headers=headers, data=data)
        if response.status_code == 200:
            content = response.content
            self._auth_info = json.loads(content.decode('utf-8'))
            return content
        else:
            raise Exception(
                f"Problem when getting Auth Token from ASG Auth Url : {self.accordAuthServer} .. response code : {response.status_code} .. body {response.content.decode()}")

    def extract_accord_data(self, byte_array):
        self.get_auth_token()
        target_url = f'{self.accordUrl}?inputFormat=PDF&outputFormat=ELABEL'
        headers = {
            'Authorization': f'{self._auth_info["access_token"]}',
            'Content-Type': 'application/json',
            'x-api-key': self.accordApiKey,
            'Accept': 'application/json'

        }
        response = requests.post(target_url, headers=headers, data=byte_array)
        if response.status_code == 202:
            content = response.content
            callback_url = json.loads(content.decode('utf-8'))
            print(callback_url)
            while self.get_results(callback_url['messageId']):
                print(f'Polling for Message ID : {callback_url["messageId"]}')
        else:
            raise Exception(
                f'Issue calling ASG Service at : {target_url} ..  response code : {response.status_code} .. body : {response.content.decode("utf-8")}')
        return self.results

    def get_results(self, messageId: str):
        call_back_url_temp = f"https://uat-api-v1-transcriber.acordsolutions.net/oauth/forms/extract/{messageId}"
        headers = {
            'Authorization': f'{self._auth_info["access_token"]}',
            'Content-Type': 'application/json',
            'x-api-key': self.accordApiKey,
            'Accept': 'application/json'

        }
        end_response = requests.get(call_back_url_temp, headers=headers)
        if end_response.status_code == 200:
            content = end_response.content
            extract_results = json.loads(content.decode('utf-8'))
            response_body = json.loads(extract_results['responseBody'])
        if 'status' not in response_body['ACORD'] or response_body['ACORD']['status'] != 'PROCESSING':
                print(extract_results)
                self.results = extract_results
                return False

        time.sleep(self._sleepSeconds)
        return True
