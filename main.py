#import numpy as np
import pandas as pd
import json
import requests
from tqdm import tqdm
import geopy.distance
import os
import math

def geocodeAndRoute(home, work, duplicates):
  global errors
  #3rd argument enables/disabled checkign of duplicate hash table
  #Recommended disabled for lists with few repetitions e.g. employee homes
  #and enabled for workplaces/delivery hubs
  home_coords, duplicates = geocode(home, duplicates, False)
  work_coords, duplicates = geocode(work, duplicates, True)
  
  if (home_coords == "ERROR"):
    return float(-1.0), duplicates
  if (work_coords == "ERROR"):
    return float(-1.0), duplicates
    
  distance = route([home_coords[0], home_coords[1], work_coords[0], work_coords[1]])
  return distance, duplicates

def geocode(postcode, duplicates, dupeSearch):
  #Function geocode(postcode) takes a list of size 2 and returns a list of size 4 of format latitude, longitude, latitude, longitude
  #for home and workplace postcodes respectively
  #url_latlng = 'https://nominatim.openstreetmap.org/search/' + urllib.parse.quote(postcode) + '?format=json'
  if (postcode in duplicates) and dupeSearch:
    #print(postcode, " ", duplicates[postcode])
    return duplicates[postcode], duplicates
  else:
    url_latlng = f'https://nominatim.openstreetmap.org/search?q={postcode}%2C+UK&format=json'
    response = requests.get(url_latlng).json()
    #print('Latitude: '+response[0]['lat']+', Longitude: '+response[0]['lon'])
    if(len(response)!=0):
      duplicates.update({postcode: (round(float(response[0]['lat']),6), round(float(response[0]['lon']),6))})
      return((round(float(response[0]['lat']),6), round(float(response[0]['lon']),6)), duplicates)
    else:
      #return -1 if server returns an error
      #print("ERROR")
      duplicates.update({postcode:"ERROR"})
      return("ERROR", duplicates)

def route(coords):
  #Function route(coords) takes a list of 4 lat/long coordinates and requests a driving route through OSRM
  #and returns the distance in format KM to 2 DP
  r = requests.get(f"http://router.project-osrm.org/route/v1/car/{coords[1]},{coords[0]};{coords[3]},{coords[2]}?overview=false")
  response = r.json()
  #print(response)
  error = {'message': 'Impossible route between points', 'code': 'NoRoute'}
  if(response != error):
    route_1 = json.loads(r.content)["routes"][0]
    return(round(float(route_1["distance"])/1000,2))
  else:
    return(float(-1.0))

def distance(coords):
  return round(float(geopy.distance.geodesic((coords[0],coords[1]),(coords[2],coords[3])).km),2)



def main():
  pd.options.mode.chained_assignment = None
  tqdm.pandas()
  
  #Read postcode information for homes and respective workplaces
  df = pd.read_csv("postcodes.csv")
  #Rename columns into appropriate format
  df = df.rename(columns={df.columns[0]: 'Homes', df.columns[1]: 'Destinations'})
  do = df
  do['Distance (KM)'] = ""
  end = len(df)
  
  s = 0
  
  if (os.path.isfile('output.csv')):
    
    print("Output file found")
    do = pd.read_csv('output.csv')
    for i in range(len(do)):
      #print(type(do['Distance (KM)'][i]))
      if do['Distance (KM)'][i] == "ERROR":
        continue
      if math.isnan(do['Distance (KM)'][i]):
        print(f"Resuming from {i}")
        s = i
        break
  else:
    print("Creating output.csv...")
    
  df = df[s:]
  s = len(df)

  duplicates = {"WF2 9NA":(53.684631,-1.53863)}

  #Core loop
  for i in tqdm(range(df.index[0],end)):
    #print(f"Calculating route {i}")
    do['Distance (KM)'][i], duplicates = geocodeAndRoute(df['Homes'][i],df['Destinations'][i], duplicates)
    do.to_csv('output.csv', encoding='utf-8',index=False)
  
  #print(f"\nSuccess Rate: {round(((s - errors) / s) *100,2)}%")

if __name__ == "__main__":
  main()

#def retired():
#  print("\nGeocoding Home Postcodes...")
#  df['HG'] = df['Homes'].progress_apply(geocode)
#  print("\nGeocoding Destination Postcodes...")
#  df['DG'] = df['Destinations'].progress_apply(geocode)
#  
#  df = df[~df["HG"].isin(['ERROR'])]
#  df = df[~df["DG"].isin(['ERROR'])]
#  
#  #df.to_csv('coords_1.csv', encoding='utf-8', index=False)
#  
#  df['Coord List'] = df['HG'] + df['DG']
#  
#  print("\nCalculating Commute Distances...")
#  df['Distance (KM)'] = df['Coord List'].progress_apply(route)
#  print("\nDone!\n")
#  df.to_csv('coords.csv', encoding='utf-8', index=False)
#  
#  dfo = df.loc[:, ['Homes','Destinations','Distance (KM)']]
#  print(dfo.head())
#  dfo.to_csv('output.csv', encoding='utf-8', index=False)
#
#  print(f"\nSuccess Rate: {round((len(dfo)/s)*100,2)}% ({len(dfo)} / {s})")
#  distance = round(dfo["Distance (KM)"].sum())
#  print(f"Average Commute Distance: {round(distance / len(dfo),2)} KM")


#request template (OSRM)
#/route/v1/{profile}/{coordinates}?alternatives={true|false}&steps={true|false}&geometries={polyline|polyline6|geojson}&overview={full|simplified|false}&annotations={true|false}