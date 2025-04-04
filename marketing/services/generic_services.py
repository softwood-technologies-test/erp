from apparelManagement.services.generic_services import convertTexttoObject, paginate, applySearch, truncateTime
from apparelManagement.services.generic_services import refineJson, concatenateValues, updateModelWithDF, LOCAL_TIMEZONE

from google import genai
import pandas as pd

import os

#API_KEY_FOR_AI = os.environ.get("API_KEY_FOR_AI")
API_KEY_FOR_AI = 'AIzaSyCAmIGtNVCJ662s67IWbmtlFw7O5-GCBUo'

def askAI(question: str):
    '''
    Ask AI a question and get it's answer
    '''
    client = genai.Client(api_key=API_KEY_FOR_AI)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=question,
    ).text

    return response

def dfToListOfDicts(df: pd.DataFrame):
    '''
    Converts a dataframe to a list of dicts
    '''

    cols = list(df.columns)

    if df.empty:
        return [{col: "" for col in cols}]
    else:
        return [dict(zip(cols, row)) for row in df.values]