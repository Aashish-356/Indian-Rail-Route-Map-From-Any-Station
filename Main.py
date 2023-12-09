import requests
from bs4 import BeautifulSoup
import folium
import pandas as pd
import random

# Load station coordinates from the CSV file
csv_file_path = 'stations.csv'
try:
    station_data = pd.read_csv(csv_file_path)
    station_coordinates = dict(zip(station_data['STN CODE'], zip(station_data['LAT'], station_data['LON'])))
except KeyError as e:
    print(f"Error: The column '{e.args[0]}' is not present in the CSV file. Please check the header.")
    exit()

def get_station_codes(train_number):
    formatted_train_number = f"{int(train_number):05d}"  # Convert to integer before formatting
    url = f"https://etrain.info/train/{formatted_train_number}/schedule"
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        source_select = soup.find('select', {'name': 'src'})

        if source_select is not None:
            station_codes = [option['value'] for option in source_select.find_all('option')]
            return station_codes
        else:
            print(f"Source station select element not found for train {formatted_train_number}")
            return None

    elif response.status_code == 404:
        print(f"Train {formatted_train_number} not found on the website.")
        return None

    else:
        print(f"Failed to retrieve data for train {formatted_train_number}. Status code: {response.status_code}")
        return None

# Fetch train numbers
station = input("Enter station code:")
url = f"https://etrain.info/station/{station}/all"
response = requests.get(url)
html_content = response.text
soup = BeautifulSoup(html_content, "html.parser")

train_numbers = []

for row in soup.find_all("tr", {"data-train": True}):
    train_data = row.get("data-train")
    if train_data:
        train_info = eval(train_data)
        train_number = train_info["num"]
        train_numbers.append(train_number)

# Create a dictionary to store station codes for each train number
train_station_dict = {}

# Fetch and store station codes for each train number
for train_number in train_numbers:
    station_codes = get_station_codes(train_number)
    if station_codes is not None:
        train_station_dict[train_number] = station_codes

# Print each element of the dictionary on a new line
print(f"Total No. of trains:{len(train_station_dict)}")
for train_number, stations in train_station_dict.items():
    print(f"{train_number}:{stations}")
    print("\n")


# Create a folium map centered at an average location
map_center = [station_data['LAT'].mean(), station_data['LON'].mean()]
train_map = folium.Map(location=map_center, zoom_start=6)

# Plot stations and connect them with lines
# ...

# Add Markers and Connect Routes with Random Colors:
added_locations = set()

for train_number, stations in train_station_dict.items():
    # Generate a random color for each train
    color = "#{:06x}".format(random.randint(0, 0xFFFFFF))

    for i in range(len(stations) - 1):
        start_station = stations[i]
        end_station = stations[i + 1]
        start_coord = station_coordinates.get(start_station)
        end_coord = station_coordinates.get(end_station)

        # Check if the locations have not been added already
        if start_coord and end_coord and start_coord not in added_locations:
            folium.Marker(start_coord, popup=start_station).add_to(train_map)
            added_locations.add(start_coord)

        if end_coord and end_coord not in added_locations:
            folium.Marker(end_coord, popup=end_station).add_to(train_map)
            added_locations.add(end_coord)

        # Connect the route only if both start and end locations are added
        if start_coord and end_coord:
            folium.PolyLine([start_coord, end_coord], color=color, weight=2.5, opacity=1).add_to(train_map)

# Save the map to an HTML file
train_map.save('train_stations_map.html')
