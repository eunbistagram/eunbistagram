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
import subprocess
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
    
    
    
#eunbistagram.py -- feed posts -------------------------------------------------------------------------------------------------------------------------------------------------------------------------
consumer_key = os.environ.get('CONSUMER_KEY')
consumer_secret = os.environ.get('CONSUMER_SECRET')
access_token = os.environ.get('ACCESS_TOKEN')
access_token_secret = os.environ.get('ACCESS_TOKEN_SECRET')
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
twtapi = tweepy.API(auth)

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
				urllib.request.urlretrieve(upload, 'posts/album-%s.jpg' % i)
			else:
				containsVideo = True
				upload = media['video_versions'][0]['url']
				filename = 'posts/album-%s.mp4'%i
				urllib.request.urlretrieve(upload, filename)
				newfileName = 'posts/album-converted_vid-%s.mp4'%i
				convertVideo(filename, newfileName)
	elif isPhoto:
		upload = post['image_versions2']['candidates'][0]['url']
		urllib.request.urlretrieve(upload, 'posts/post.jpg')
		
	elif isVideo:
		upload = post['video_versions'][0]['url']
		filename = 'posts/post.mp4'
		urllib.request.urlretrieve(upload, filename)
		newfileName = 'posts/post-converted.mp4'
		convertVideo(filename, newfileName)
		
	else:
		print('Unidentified media type\n')
		print(post['media_type'])
		print(isAlbum, isPhoto, isVideo)
		sys.exit()

def convertVideo(filename, newfilename):
	convert_cmd = ['ffmpeg', '-i', filename, '-vcodec', 'libx264', newfilename]
	subprocess.run(convert_cmd)
	os.remove(filename)
	
	
def getMediaFile():
	media_files = []
	for f in os.listdir('posts/'):
		media_files.append('posts/%s' % f)
	return media_files



def tweetPost(media_files):

	vid_ids = []
	pic_ids = []

	if containsVideo:
		for item in media_files:
			if '.jpg' in item:
				pic_ids.append(twtapi.media_upload(item).media_id)
			else:
				vid_ids.append(item)
		
		if len(vid_ids) == 0:
			if len(pic_ids) <= 4:
				twtapi.update_status(media_ids=pic_ids, status='[%s INSTAGRAM CAROUSEL]'%getTimeStamp(latest_post))
			elif len(pic_ids) <= 8:
				post1 = twtapi.update_status(media_ids=pic_ids[0:4], status='[%s INSTAGRAM CAROUSEL]'%getTimeStamp(latest_post))
				post2 = twtapi.update_status(media_ids=pic_ids[4::], status='', in_reply_to_status_id=post1.id)
			elif len(pic_ids) <= 10:
				post1 = twtapi.update_status(media_ids=pic_ids[0:4], status='[%s INSTAGRAM CAROUSEL]'%getTimeStamp(latest_post))
				post2 = twtapi.update_status(media_ids=pic_ids[4:8], status='', in_reply_to_status_id=post1.id)
				post3 = twtapi.update_status(media_ids=pic_ids[8::], status='', in_reply_to_status_id=post2.id)
			else:
				print('Error at tweetPost and containsVideo. More than 10 pics possibly')
				
		elif len(pic_ids) == 0:
			post = postVideoTweet('[%s INSTAGRAM CAROUSEL]'%getTimeStamp(latest_post), None, vid_ids[0])
			vid_ids.pop(0)
			for vid in vid_ids:
				post = postVideoTweet('', post.id, vid)
		
		else:
			if len(pic_ids) <= 4:
				post = twtapi.update_status(media_ids=pic_ids, status='[%s INSTAGRAM CAROUSEL]'%getTimeStamp(latest_post))
				for vid in vid_ids:
					post = postVideoTweet('', post.id, vid)
					
			elif len(pic_ids) <= 8:
				post = twtapi.update_status(media_ids=pic_ids[0:4], status='[%s INSTAGRAM CAROUSEL]'%getTimeStamp(latest_post))
				post = twtapi.update_status(media_ids=pic_ids[4::], status='', in_reply_to_status_id=post.id)
				for vid in vid_ids:
					post = postVideoTweet('', post.id, vid)
					
			elif len(pic_ids) <= 10:
				post = twtapi.update_status(media_ids=pic_ids[0:4], status='[%s INSTAGRAM CAROUSEL]'%getTimeStamp(latest_post))
				post = twtapi.update_status(media_ids=pic_ids[4:8], status='', in_reply_to_status_id=post.id)
				post = twtapi.update_status(media_ids=pic_ids[8::], status='', in_reply_to_status_id=post.id)
				for vid in vid_ids:
					post = postVideoTweet('', post.id, vid)
			else:
				print('Error at tweetPost and containsVideo. More than 10 pics possibly.')
			


	elif isAlbum and not containsVideo:
		for item in media_files:
			pic_ids.append(twtapi.media_upload(item).media_id)
		if len(pic_ids) <= 4:
			twtapi.update_status(media_ids=pic_ids)
		elif len(pic_ids) <= 8:
			post1 = twtapi.update_status(media_ids=pic_ids[0:4], status='[%s INSTAGRAM CAROUSEL]'%getTimeStamp(latest_post))
			post2 = twtapi.update_status(media_ids=pic_ids[4::], status='', in_reply_to_status_id=post1.id)
		elif len(pic_ids) <=10:
			post1 = twtapi.update_status(media_ids=pic_ids[0:4], status='[%s INSTAGRAM CAROUSEL]'%getTimeStamp(latest_post))
			post2 = twtapi.update_status(media_ids=pic_ids[4:8], status='', in_reply_to_status_id=post1.id)
			post3 = twtapi.update_status(media_ids=pic_ids[8::], status='', in_reply_to_status_id=post2.id)
		else:
			print('Error at tweetPost. isAlbum and not containsVideo. More than 10 images')
	
	elif isPhoto:
		for item in media_files:
			pic_ids.append(twtapi.media_upload(item).media_id)
		twtapi.update_status(media_ids=pic_ids, status= '[%s INSTAGRAM PHOTO]'%getTimeStamp(latest_post))
	elif isVideo:
		for item in media_files:
			vid_ids.append(item)
		post = postVideoTweet('[%s INSTAGRAM VIDEO]'%getTimeStamp(latest_post), None, vid_ids[0])
		
	else:
		print('Problem at tweetPost')
		


latest_post = findPost(getFeed(EUNBI_ID), 0)

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
	tweetPost(media_files)
else:
	print('No new update')
	









#eunbistagram.py --- story posts -----------------------------------------------------------------------------------------------------------------------------------------------------------------------

story_reel = api.user_story_feed(EUNBI_ID)['reel']
if story_reel == None:
	print('No live stories on instagram.com/silver_rain.__')
	sys.exit();

story_items = story_reel['items']
	
def saveStory(story_items, newposts):
	for i, media in enumerate(story_items):
		if media['taken_at'] in newposts:
			if media['media_type'] == 2:
				story = media['video_versions'][0]['url']
				filename = 'stories/story-%s.mp4'%i
				urllib.request.urlretrieve(story, 'stories/story-%s.mp4' %i)
				newfilename = 'stories/converted_story-%s.mp4'%i
				convertVideo(filename, newfilename)
			elif media['media_type'] == 1:
				story = media['image_versions2']['candidates'][0]['url']
				urllib.request.urlretrieve(story, 'stories/story-%s.jpg' %i)
			else:
				print('Error at saveStory')
				sys.exit()
		else:
			continue
			
def getStoryFile():
	story_files = []
	for f in os.listdir('stories'):
		story_files.append('stories/%s' % f)
	return story_files
	
	
def identifyStoryType(story_files):
	global containsVideo
	containsVideo = False
	for item in story_files:
		if '.mp4' in item:
			containsVideo = True

def tweetStory(story_files):
	identifyStoryType(story_files)
	vid_ids = []
	pic_ids = []
	if containsVideo:
		for item in story_files:
			if '.jpg' in item:
				pic_ids.append(twtapi.media_upload(item).media_id)
			else:
				vid_ids.append(item)

	if len(vid_ids) == 0:
		if len(pic_ids) <= 4:
			twtapi.update_status(media_ids=pic_ids, status='test')
		elif len(pic_ids) <= 8:
			story1 = twtapi.update_status(media_ids=pic_ids[0:4], status='[%s INSTAGRAM STORY]'%getTimeStamp(story_items[0]))
			story2 = twtapi.update_status(media_ids=pic_ids[4::], status='', in_reply_to_status_id=story1.id)
		elif len(pic_ids) <= 10:
			story1 = twtapi.update_status(media_ids=pic_ids[0:4], status='[%s INSTAGRAM STORY]'%getTimeStamp(story_items[0]))
			story2 = twtapi.update_status(media_ids=pic_ids[4:8], status='', in_reply_to_status_id=story1.id)
			story3 = twtapi.update_status(media_ids=pic_ids[8::], status='', in_reply_to_status_id=story2.id)
		else:
			print('Error at tweetStory. More than 10 story images')
			
	elif len(pic_ids) == 0:
		story = postVideoTweet('[%s INSTAGRAM STORY]'%getTimeStamp(story_items[0]), None, vid_ids[0])
		vid_ids.pop(0)
		for vid in vid_ids:
			story = postVideoTweet('', story.id, vid)
	else:
		if len(pic_ids) <= 4:
			story = twtapi.update_status(media_ids=pic_ids, status='[%s INSTAGRAM STORY]'%getTimeStamp(story_items[0]))
			for vid in vid_ids:
				story = postVideoTweet('', story.id, vid)
			
		elif len(pic_ids) <= 8:
			story = twtapi.update_status(media_ids=pic_ids[0:4], status='[%s INSTAGRAM STORY]'%getTimeStamp(story_items[0]))
			story = twtapi.update_status(media_ids=pic_ids[4::], status='', in_reply_to_status_id=story.id)
			for vid in vid_ids:
				story = twtapi.update_status(media_ids=vid, in_reply_to_status_id=story.id)
		elif len(pic_ids) <= 10:
			story = twtapi.update_status(media_ids=pic_ids[0:4], status='[%s INSTAGRAM STORY]'%getTimeStamp(story_items[0]))
			story = twtapi.update_status(media_ids=pic_ids[4:8], status='', in_reply_to_status_id=story.id)
			story = twtapi.update_status(media_ids=pic_ids[8::], status='', in_reply_to_status_id=story.id)
			for vid in vid_ids:
				story = twtapi.update_status(media_ids=vid, in_reply_to_status_id=story.id)
		else:
			print('Error at tweetStory. More than 10 story images with some videos')
			
def postVideoTweet(status, reply_id, filename):
	print(filename)
	uploaded_media = twtapi.media_upload(filename, media_category='TWEET_VIDEO')
	while (uploaded_media.processing_info['state'] == 'pending'):
		time.sleep(uploaded_media.processing_info['check_after_secs'])
		uploaded_media = twtapi.get_media_upload_status(uploaded_media.media_id)
	time.sleep(10)
	print([uploaded_media.media_id])
	print('\n\n\n')
	return twtapi.update_status(status=status, in_reply_to_status_id=reply_id, auto_populate_reply_metadata = True, media_ids=[uploaded_media.media_id])
    
    			
			
with open ('storytimes.txt', 'a+') as storylogs:
	newposts = []
	for i, media in enumerate(story_items):
		timestamp = media['taken_at']
		storylogs.seek(0)
		logs = storylogs.read();
		if str(timestamp) not in logs:
			newposts.append(timestamp)
			storylogs.write(str(timestamp) + '\n')



			
if len(newposts) > 0:
	saveStory(story_items, newposts)
	story_files = getStoryFile()
	identifyStoryType(story_files)
	tweetStory(story_files)
else:
	print('No new story update')
	sys.exit()

