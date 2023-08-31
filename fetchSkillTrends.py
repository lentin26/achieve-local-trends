from dotenv import dotenv_values
import requests
import numpy as np 
import pandas as pd


class fetchSkillTrends:

    def __init__(self):
        config = dotenv_values(".env")

        self.FAETHM_ACCESS_TOKEN = config["FAETHM_ACCESS_TOKEN"]         # expired access token from Faethm hackathon

        self.base_url = "https://au.aws.api.development.faethm.ai"
        self.endpoint = "/di/v1/insights/skill_trends"
        self.headers = {"Authorization": "Bearer {}".format(self.FAETHM_ACCESS_TOKEN), "Content-Type": "application/json"}

        self.responses = None
        self.response_statuses = None

    def fetch_skills(self, skill_ids, country_code='US', start_date=None):

        # format request payload
        data = {
            "skill_id": None,
            "country_code": country_code
        }

        # add optional start date to payload if not None
        if start_date:
            data["start_date"] = start_date

        # get skill demand
        responses = []
        response_statuses = []
        for skill_id in skill_ids:
            data["skill_id"] = skill_id

            # request
            r = requests.get(
                self.base_url + self.endpoint, 
                params=data, 
                headers=self.headers
            )

            # append response and response code 
            responses.append(r.json())
            response_statuses.append(r.status_code)

        self.responses = responses
        self.response_statuses = response_statuses

        # raise exception if recieved response code other than 200
        if not (np.array(response_statuses) == 200).all():
            raise Exception('Response status other than OK 200:', response_statuses)

        # # convert results to dataframe and return
        # skill_trends = pd.DataFrame(response['skill_trends']) 
