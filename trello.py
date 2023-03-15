import http.client
import urllib.parse
import json
import argparse

# Set up command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-n", "--name", required=True, help="Name of the new Trello card")
parser.add_argument("-c", "--comment", help="Comment to add to the new Trello card")
args = parser.parse_args()

# Set up Trello API credentials
key = "2953fdf6980be85cad08a5f91f079a2a"
token = "ATTA4f229a1bd7e7c68fd16e0b54060637ac5ad0c8269b5ea2ac657a059a9bbdb186DDB131B4"
board_id = "63fdecb3fb216bc53999b7c6"

# Set up API URL and parameters for creating a new card
url = "/1/cards"
params = {
    "key": key,
    "token": token,
    "idList": board_id,
    "name": args.name
}

# If a comment was provided, add it to the parameters
if args.comment:
    params["desc"] = args.comment

# Set the Content-Type header to application/json
headers = {
    "Content-Type": "application/json"
}

# Encode the parameters as JSON
data = json.dumps(params)

# Create an HTTPS connection to the Trello API server
conn = http.client.HTTPSConnection("api.trello.com")

# Send a POST request to create the new card
conn.request("POST", url, body=data, headers=headers)

# Read the response from the server
response = conn.getresponse()

# Check the response status code and print a message indicating success or failure
if response.status == 200:
    print(f"New card '{args.name}' created successfully.")
    if args.comment:
        print(f"Comment '{args.comment}' added to card.")
else:
    print("Error creating new card:")
    print(response.read().decode())

# Close the HTTP connection
conn.close()
