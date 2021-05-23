#! /usr/bin/python3
import tweepy
import instaloader
import itertools

L = instaloader.Instaloader()
acc = 'silver_rain.__'

profile = instaloader.Profile.from_username(L.context, acc)

print("{} follows these profiles:".format(profile.username))

print([x for followee in profile.get_followees()])
