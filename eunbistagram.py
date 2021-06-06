import json
import codecs
import datetime
import os.path
import logging
import argparse
import urllib
from pathlib import Path
import datetime as dt
import time
import sys
import pytz
import os
import tweepy

#save_settings + login callback script
try:
    from instagram_private_api import (
        Client, ClientError, ClientLoginError,
        ClientCookieExpiredError, ClientLoginRequiredError,
        __version__ as client_version)
except ImportError:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from instagram_private_api import (
        Client, ClientError, ClientLoginError,
        ClientCookieExpiredError, ClientLoginRequiredError,
        __version__ as client_version)


def to_json(python_object):
    if isinstance(python_object, bytes):
        return {'__class__': 'bytes',
                '__value__': codecs.encode(python_object, 'base64').decode()}
    raise TypeError(repr(python_object) + ' is not JSON serializable')


def from_json(json_object):
    if '__class__' in json_object and json_object['__class__'] == 'bytes':
        return codecs.decode(json_object['__value__'].encode(), 'base64')
    return json_object


def onlogin_callback(api, new_settings_file):
    cache_settings = api.settings
    with open(new_settings_file, 'w') as outfile:
        json.dump(cache_settings, outfile, default=to_json)
        print('SAVED: {0!s}'.format(new_settings_file))


if __name__ == '__main__':

    logging.basicConfig()
    logger = logging.getLogger('instagram_private_api')
    logger.setLevel(logging.WARNING)

    # Example command:
    # python examples/savesettings_logincallback.py -u "yyy" -p "zzz" -settings "test_credentials.json"
    parser = argparse.ArgumentParser(description='login callback and save settings')
    parser.add_argument('-settings', '--settings', dest='settings_file_path', type=str, required=True)
    parser.add_argument('-u', '--username', dest='username', type=str, required=True)
    parser.add_argument('-p', '--password', dest='password', type=str, required=True)
    parser.add_argument('-debug', '--debug', action='store_true')

    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)

    print('Client version: {0!s}'.format(client_version))

    device_id = None
    try:

        settings_file = args.settings_file_path
        if not os.path.isfile(settings_file):
            # settings file does not exist
            print('Unable to find file: {0!s}'.format(settings_file))

            # login new
            api = Client(
                args.username, args.password,
                on_login=lambda x: onlogin_callback(x, args.settings_file_path))
        else:
            with open(settings_file) as file_data:
                cached_settings = json.load(file_data, object_hook=from_json)
            print('Reusing settings: {0!s}'.format(settings_file))

            device_id = cached_settings.get('device_id')
            # reuse auth settings
            api = Client(
                args.username, args.password,
                settings=cached_settings)

    except (ClientCookieExpiredError, ClientLoginRequiredError) as e:
        print('ClientCookieExpiredError/ClientLoginRequiredError: {0!s}'.format(e))

        # Login expired
        # Do relogin but use default ua, keys and such
        api = Client(
            args.username, args.password,
            device_id=device_id,
            on_login=lambda x: onlogin_callback(x, args.settings_file_path))

    except ClientLoginError as e:
        print('ClientLoginError {0!s}'.format(e))
        exit(9)
    except ClientError as e:
        print('ClientError {0!s} (Code: {1:d}, Response: {2!s})'.format(e.msg, e.code, e.error_response))
        exit(9)
    except Exception as e:
        print('Unexpected Exception: {0!s}'.format(e))
        exit(99)

    # Show when login expires
    cookie_expiry = api.cookie_jar.auth_expires
    print('Cookie Expiry: {0!s}'.format(datetime.datetime.fromtimestamp(cookie_expiry).strftime('%Y-%m-%dT%H:%M:%SZ')))

    # Call the api
    results = api.user_feed('2958144170')
    assert len(results.get('items', [])) > 0

    print('All ok')
    
    
    
#eunbistagram.py
EUNBI_ID = '47636361181'
UUID = api.generate_uuid(return_hex=False, seed=None);

def getFeed(userID):
	user_feed = api.user_feed(userID)
	feed_items = user_feed.get('items')
	return feed_items
	
def findPost(feed, index):
	post = feed[index]
	return post



	
def getTimeStamp(post):
	timestamp = post['taken_at']
	formatted_time = dt.datetime.fromtimestamp(timestamp)
	korea_time = formatted_time.astimezone(pytz.timezone('Asia/Seoul'))
	return korea_time.strftime('%y%m%d')
	


isVideo = False
isAlbum = False
isPhoto = False
containsVideo = False

def identifyMediaType(media):
	global isAlbum
	global isPhoto
	global isVideo
	media_type = media['media_type']
	if media_type == 8:
		isAlbum = True
		
	elif media_type == 2:
		isVideo = True
	else:
		isPhoto = True
		

def saveMedia(post):
	global containsVideo
	identifyMediaType(post)
	if isAlbum:
		album = post['carousel_media']
		for i, media in enumerate(album):
			identifyMediaType(media)
			if isPhoto:
				upload = media['image_versions2']['candidates'][0]['url']
				urllib.request.urlretrieve(upload, 'album-%s-P.jpg' % i)
			else:
				containsVideo = True
				upload = media['video_versions'][0]['url']
				urllib.request.urlretrieve(upload, 'album-%s-V.mp4' % i)
	elif isPhoto:
		upload = post['image_versions2']['candidates'][0]['url']
		urllib.request.urlretrieve(upload, 'img.jpg')
		
	elif isVideo:
		upload = post['video_versions'][0]['url']
		urllib.request.urlretrieve(upload, 'video.mp4')
		
	else:
		print('Unidentified media type\n')
		print(post['media_type'])
		print(isAlbum, isPhoto, isVideo)
		sys.exit()

	
def getMediaFile():
	media_files = []
	for f in os.listdir('.'):
		if os.path.isfile(f) and 'album-' in f:
			media_files.append(f)
		elif os.path.isfile(f) and 'img' in f:
			media_files = f
		elif os.path.isfile(f) and 'video' in f:
			media_files = f
		else:
			continue
			
	return media_files
	

latest_post = findPost(getFeed(EUNBI_ID), 0)

saveMedia(latest_post)

	
new = True

with open ('timestamps.txt', 'a+') as logfile:
	timestamp = latest_post['taken_at']
	logfile.seek(0)
	logs = logfile.read();
	if str(timestamp) in logs:
		new = False
	else:
		new = True
		logfile.write(str(timestamp) + '\n')
if new:
	saveMedia(latest_post)
	media_files = getMediaFile()
else:
	print('No new update')
	sys.exit();
	

consumer_key = os.environ.get('CONSUMER_KEY')
consumer_secret = os.environ.get('CONSUMER_SECRET')
access_token = os.environ.get('ACCESS_TOKEN')
access_token_secret = os.environ.get('ACCESS_TOKEN_SECRET')

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)


media_ids = []

#if containsVideo:
	#media_ids.append(media_files

for i, media in enumerate(media_files):
	media_ids.append(api.media_upload(media).media_id_string)


if isAlbum and not containsVideo:
	if len(media_ids) <= 4:
		api.update_status(media_ids=media_ids, status='test')
	elif len(media_ids) <= 8:
		post1 = api.update_status(media_ids=media_ids[0:4], status='test')
		post2 = api.update_status(media_ids=media_ids[4::], status='test2', in_reply_to_status_id=post1.id)
	else:
		print('more than 8 images')

#jun 5 9:10pm MST - added image uploading + tweeting
#work on formatting tweets next


	
	

