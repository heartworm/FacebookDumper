import requests
import json
import os
import time

# The ID of your group chat, and your facebook User ID
group_id = ""
user_id = ""

# Values used to authenticate you, obtain them from your browser's developer tools. __dyn, fb_dtsg and your HTTP cookie.
dyn = ""
fb_dtsg = ""
cookie = ""

# Less important values
req = "1" # Req value from your XHR requests, doesn't seem to affect much
logging = "" # Logging value from XHR, doesn't seem to affect much
rev = "" # Rev value from XHr, also seems fairly innocuous

# Message retrieval settings
chunk_size = 10000 # How many messages to request at a time, the server seems happy with 10000
beginning_offset = 0 # Where to start from, untested with values other than 0
beginning_timestamp = "" # Leave this blank, used to request messages prior to a certain timestamp.
request_delay = 1 # in seconds, how long to wait before sending another message request. Avoid rate limiting by facebook

# Actual program below.------------------------------------------------------------

thread_id = "messages[thread_fbids][{}]".format(group_id)

request_url = "https://www.messenger.com/ajax/mercury/thread_info.php?dpr=1"

request_headers = {
    "origin": "https://www.messenger.com",
    "accept": "*/*",
    "cache-control": "no-cache",
    "referer": "https://www.messenger.com/t/{}".format(group_id),
    "accept-encoding": "gzip, deflate",
    "accept-language": "en-US,en;q=0.4",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)"
                  " Chrome/58.0.3029.110 Safari/537.36",
    "x-msgr-region": "FRC",
    "cookie": cookie
}

request_data = {
    thread_id + "[offset]": "0",
    thread_id + "[limit]": "20",
    thread_id + "[timestamp]": "",

    "__user": user_id,
    "__dyn": dyn,
    "fb_dtsg": fb_dtsg,
    "__rev": rev,
    "logging": logging,
    "__req": req,

    "client": "mercury",
    "__af": "iw",
    "__a": "1",
    "__be": "-1",
    "__pc": "PHASED:messengerdotcom_pkg",
}


def request_message_json(offset, limit, timestamp):
    request_data[thread_id + "[timestamp]"] = str(timestamp)
    request_data[thread_id + "[offset]"] = str(offset)
    request_data[thread_id + "[limit]"] = limit

    response = requests.post(request_url, data=request_data, headers=request_headers)
    if response.status_code != 200:
        print("Server's response code wasn't 200 (OK), returning None in get_json")
        return None
    else:
        json_text = response.text[response.text.find("{"):]
        json_obj = None

        try:
            json_obj = json.loads(json_text)
        except json.JSONDecodeError:
            print("Didn't get a valid JSON response from Facebook. Got this instead:")
            print(json_text)
            exit(1)

        return json_obj, json_text


def write_json_file(filename, json_text):
    with open(filename, 'w') as out_file:
        out_file.write(json_text)
        print("Wrote file " + filename)

# Make the output directory, stop if it exists cause we don't wanna overwrite anything.
out_dir = str(group_id)
if not os.path.exists(out_dir):
    os.makedirs(out_dir)
else:
    print("Output directory '{}' already exists, quitting.".format(out_dir))
    exit(1)
os.chdir(out_dir)

# Main loop.
obtaining_messages = True
current_offset = beginning_offset
current_timestamp = beginning_timestamp
while obtaining_messages:
    time.sleep(request_delay)

    print("Getting messages from {} to {} from timestamp {}".format(current_offset, current_offset+chunk_size,
                                                                    current_timestamp))

    json_obj, json_text = request_message_json(current_offset, chunk_size, current_timestamp)
    if "payload" not in json_obj:
        print("JSON Object from server didn't include a payload for some reason! Got this instead:")
        print(json_obj)
        break

    payload = json_obj["payload"]
    if json_obj is not None:
        if "end_of_history" in payload:
            print("Found the end of the message history. Ending dump.")
            obtaining_messages = False  # reached end of history

        if "actions" in payload:
            actions_list = payload["actions"]
            recvd_action_count = len(actions_list)
            print("Actually got {} messages from server.".format(recvd_action_count))
            recvd_action_count = chunk_size if recvd_action_count > chunk_size else recvd_action_count


            # set conditions for next loop
            old_offset = current_offset
            current_offset = current_offset + recvd_action_count
            current_timestamp = actions_list[0]["timestamp"]

            filename = "{}-{}.json".format(old_offset, current_offset)
            write_json_file(filename, json_text)
        else:
            print("Couldn't find the actions object in the JSON payload! Check the user details")
            obtaining_messages = False
    else:
        print("Got nothing instead of some JSON!")
        obtaining_messages = False
