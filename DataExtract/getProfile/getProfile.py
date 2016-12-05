#!/usr/local/bin/python3.5
import asyncio
from aiohttp import ClientSession

import bs4
import pandas

import requests
import re, os

headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36"}
file_path = 'Profiles'
file_enum = ['Profile_Men.csv', 'Profile_Women.csv', 'Profile_Master_Men_45.csv', 'Profile_Master_Women_45.csv',
             'Profile_Master_Men_50.csv', 'Profile_Master Women_50.csv', 'Profile_Master_Men_55.csv', 'Profile_Master_Women_55.csv',
             'Profile_Master_Men_60.csv', 'Profile_Master_Women_60.csv', 'Profile_Team.csv', 'Profile_Master_Men_40.csv',
             'Profile_Master_Women_40.csv', 'Profile_Teen_Boy_14.csv', 'Profile_Teen_Girl_14.csv', 'Profile_Teen_Boy_16.csv',
             'Profile_Teen_Girl_16.csv']

class getProfile():    
    async def downloadPage(self, sem, url, session):
        async with sem:
            return await self.getPage(url, session)
    
    async def getPage(self, url, session):
        async with session.get(url, headers=headers) as response:
            data = await response.text()
            return data
            
    async def loopPages(self, Id_list):
        async_list = []
        sem = asyncio.Semaphore(1000) #create semaphore
        
        async with ClientSession() as session:
            for profile in Id_list:
                url = 'http://games.crossfit.com/athlete/' + str(profile)
                task = asyncio.ensure_future(self.downloadPage(sem, url, session))
                async_list.append(task)
            results = await asyncio.gather(*async_list) 
        #loop through pages on complete
        for page in results:
            self.getStats(page)            

    def getStats(self, response):
        soup = bs4.BeautifulSoup(response, "html.parser")
        
        #grab name, affiliate
        name = soup.find(id="page-title").string.extract()
        name = name[9:]
        affiliate_txt = soup.find("dt", text="Affiliate:")
        if affiliate_txt:
            affiliate_txt = affiliate_txt.next_sibling.string
         
        #collect age, height, weight
        age = int(soup.find("dt", text="Age:").next_sibling.string)
        height_txt = soup.find("dt", text="Height:").next_sibling.string

        m = [int(s) for s in re.findall(r'\d+', height_txt)]
        if "cm" in height_txt: #cm to inch
            height = int(int(height_txt[:2])*0.393701)
        elif m: #feet' inch" to inches
            height = int((m[0] * 12) + m[1])
        else:
            height = 0

        weight_txt = soup.find("dt", text="Weight:").next_sibling.string
        weight = self.convertWeight(weight_txt)

        #collect maxes
        sprint = soup.find("td", text="Sprint 400m").next_sibling.string
        clean_jerk_txt = soup.find("td", text="Clean & Jerk").next_sibling.string
        clean_jerk = self.convertWeight(clean_jerk_txt)
        snatch_txt = soup.find("td", text="Snatch").next_sibling.string
        snatch = self.convertWeight(snatch_txt)
        deadlift_txt = soup.find("td", text="Deadlift").next_sibling.string
        deadlift = self.convertWeight(deadlift_txt)
        back_squat_txt = soup.find("td", text="Back Squat").next_sibling.string
        back_squat = self.convertWeight(back_squat_txt)
        pullup_txt = soup.find("td", text="Max Pull-ups").next_sibling.string
        if "--" in pullup_txt:
            pullups = int(0)
        else: 
            pullups = int(pullup_txt)
        
        self.Athletes.loc[name] = (affiliate_txt, age, height, weight, sprint, clean_jerk, snatch, deadlift, back_squat, pullups)
    
    def convertWeight(self, kilos):
        if "kg" in kilos:
            return int(int(kilos[:-3])*2.20462) #kg to lbs
        elif "--" in kilos:
            return 0
        else:
            return int(kilos[:-3]) #drop "lbs"
    
    def __init__(self, Id_list, div):
        self.Athletes = pandas.DataFrame(columns=('Affiliate', 'Age', 'Height', 'Weight', 'Sprint 400m', 
                                        'Clean & Jerk', 'Snatch', 'Deadlift', 'Back Squat', 'Max Pull-ups')) 
        async_list = []
        
        #loop through the athlete ID list accessing each profile
        print(str(len(Id_list)) + " athletes in this division")
 
        #loop through the pages
        loop = asyncio.get_event_loop()
        future = asyncio.ensure_future(self.loopPages(Id_list))
        print("Downloading " + str(len(Id_list)) + " athlete profiles...")
        loop.run_until_complete(future)
  
        filename = os.path.join(file_path, file_enum[int(div)-1])
        self.Athletes.to_csv(path_or_buf=filename)
        print(filename + " written out.")
        
   
  