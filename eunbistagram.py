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
    
    


#generate uuid    
uuid = api.generate_uuid(return_hex=False, seed=None);

#initialize variable for user's following list, iterate and print followings
eunbi_following = api.user_following('47636361181', uuid).get('users')
for user in eunbi_following:
	print(user['username'])

#store the user's feed in a variable	
eunbi_feed = api.user_feed('47636361181')
feed_items = eunbi_feed.get('items')

#retreive the user's latest feed item (post)
latest_post = feed_items[1]

#retreive latest post's timestamp, format it
timestamp = latest_post['taken_at']
formatted_time = dt.datetime.fromtimestamp(timestamp)
print(formatted_time)


#list all the metadata tags on the latest post
tags = list(latest_post.keys())


#if the post is a carousel(album)
if 'carousel_media' in tags:
	print('It\'s an album!\n')
	time.sleep(1)
	#store the carousel object in a variable, print the largest image size for each photo
	album_media = latest_post['carousel_media']
	for i, photo in enumerate(album_media):
		#store the upload url in a variable, access the url and save the image
		upload = photo['image_versions2']['candidates'][0]['url']
		urllib.request.urlretrieve(upload, 'photo-%s.jpg' % i)


#else if it's just a photo
else:
	print('Not an album!\n')
	time.sleep(1)
	#store the upload url in a variable, access the url and save the image
	upload = latest_post['image_versions2']['candidates'][0]['url']
	urllib.request.urlretrieve(upload, "photo.jpg")




