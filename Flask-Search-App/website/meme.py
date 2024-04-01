#import necessary libraries
import asyncio
import aiohttp
import pycurl
import json
import time
from io import BytesIO
import re
import pprint
from .models import data_sources
from . import db
from sqlalchemy.inspection import inspect
import ast

def perform_ntlm_authenticated_request(url, username, password):
    buffer = BytesIO()
    curl = pycurl.Curl()
    curl.setopt(pycurl.URL, url)
    curl.setopt(pycurl.USERPWD, f"{username}:{password}")
    curl.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_NTLM)
    curl.setopt(pycurl.WRITEFUNCTION, buffer.write)
    
    # Disable TLS verification
    curl.setopt(pycurl.SSL_VERIFYPEER, False)
    curl.setopt(pycurl.SSL_VERIFYHOST, False)
    
    curl.perform()
    curl.close()
    body = buffer.getvalue().decode('utf-8')
    buffer.close()
    return body

def findFolders(listFolder,out):
    #out = []
    #print("def was call for listFolder ID = " + str(listFolder))
    out.append(listFolder)
    username = "administrator"
    password = "77@NguyenQuyDuc"
    #for i in range(len(listFolder)):
    url = "https://192.168.10.202/pivision/utility/api/v1/folders?folderid="+str(listFolder)
    childfolder_json = json.loads(perform_ntlm_authenticated_request(url,username,password))
    for Id in range(len(childfolder_json["Items"])):
        #print("loop in "+str(Id))
        #out.append(childfolder_json["Items"][Id]["Id"])
        #print(childfolder_json["Items"][Id]["Id"])
        if childfolder_json["Items"][Id]["HasChildren"] == True:
            findFolders(childfolder_json["Items"][Id]["Id"],out)
    #print("done loop in")
    return None

def findDislays(folderId,display_id):
    username = "administrator"
    password = "77@NguyenQuyDuc"
    for Id in folderId:
        url = f"https://192.168.10.202/pivision/utility/api/v1/displays?folderid={Id}"
        display_json = json.loads(perform_ntlm_authenticated_request(url,username,password))
        for k in range(len(display_json["Items"])):
            display_id.append(display_json["Items"][k]["Id"])
    return None

async def fetch_data(url,username,password):        
    temp_source = []  
    display_dict = {} 
    display_json = json.loads(perform_ntlm_authenticated_request(url,username,password))
    for symbol in range(len(display_json["Display"]["Symbols"])):
        if "DataSources" in display_json["Display"]["Symbols"][symbol]:
            #print(display_json["Display"]["Symbols"][symbol]["DataSources"])
            temp_source.append(display_json["Display"]["Symbols"][symbol]["DataSources"])
        display_dict[display_json["Display"]["Name"]] = temp_source
    #print("Task done for display "+str(time.time()-start_time)+ " for "+str(display_json["Display"]["Id"]))

    return display_dict
        
async def fetch_all_data(urls,username,password):
    tasks = []
    for url in urls:
        task = asyncio.create_task(fetch_data(url,username,password))
        tasks.append(task)
    res = await asyncio.gather(*tasks)
    #tasks = [fetch_data(url,username,password,display_dict) for url in urls]
    # Merge dictionaries
    merged_dict = {}
    for display_data in res:
        for display_name, data_sources in display_data.items():
            if display_name not in merged_dict:
                merged_dict[display_name] = data_sources
            else:
                merged_dict[display_name].extend(data_sources)
    
    return merged_dict

def search_wildcards(inputDict, keywords):
    keywords = '*'+keywords+'*'
    regexPattern = re.compile(keywords.replace('*', '.*'),re.IGNORECASE)
    print(regexPattern)
    res = dict(filter(lambda item: regexPattern.match(item[0]), inputDict.items()))
    return res


async def main(urls,username,password):   
    jsons = {}
    async with aiohttp.ClientSession() as session:
        jsons = await fetch_all_data(urls,username,password)
    return jsons


async def memify():
    start_time = time.time()
    listFolder = ""
    out=[]
    username = "administrator"
    password = "77@NguyenQuyDuc"
    findFolders(listFolder,out) #now 'out' list has been filled
    print("Exec time lasted --- %s seconds ---" % (time.time() - start_time))

    display_id = [] 
    allFolders = out
    findDislays(allFolders,display_id)
    display_id.sort()
    print("Exec time lasted --- %s seconds ---" % (time.time() - start_time))

    urls = [f"https://192.168.10.202/pivision/utility/api/v1/displays/{graphic}/export" for graphic in display_id]
    
    jsons = await main(urls,username,password)

    inverse = {}
    for k, v in jsons.items():
        if v != []:
            for x in v:
                if isinstance(x, list):
                    for item in x:
                        inverse.setdefault(item, set()).add(k)
                else:
                    inverse.setdefault(x, set()).add(k)
    

    if data_sources.query.count() != 0:
        # Clear existing data from the table
        db.session.query(data_sources).delete()

    sources_to_add = [data_sources(name=key,display=json.dumps(value)) for key, value in inverse.items()]

    #add all new data sources
    db.session.add_all(sources_to_add)
    db.session.commit()
    return str(len(inverse))

# Function to safely convert string to list using ast.literal_eval
def convert_to_list(value):
    try:
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        # If the value cannot be converted, return it as is
        return value

def convert_to_set(value):
    try:
        return {ast.literal_eval(value)}
    except (SyntaxError, ValueError):
        # If the value cannot be converted, return it as is
        return {value}