from google.appengine.ext import db
from google.appengine.api import users

#The sitewide group should exist before adding any user. The group_name is "sitewide"


#Sitewide is represented as a group in which all users are part of
class Group(db.Model):
	group_name = db.StringProperty()
	is_classroom = db.BooleanProperty(default = False) #This is set to true if the group represents a classroom
	
	@property
	def members(self):
		return User.all().filter('groups', self.key())



# User
class User(db.Model):
	user_name = db.StringProperty()
	password_MD5ed = db.StringProperty()
	groups = db.ListProperty(db.Key)
	is_teacher_of = db.ListProperty(db.Key)
	is_administrator = db.BooleanProperty(default = False)


# Datamodel for messages 
class Message(db.Model):
#	recipients = db.ListProperty(db.Key) This can get too big (sitewide messages) and groups (100k+)
	remitent =  db.ReferenceProperty(User)
	date_sent = db.DateTimeProperty()
	subject = db.StringProperty()
	group = db.ReferenceProperty(Group) #Is this a group message?
	content = db.TextProperty()

# The data model for user's inbox. Done
# possible improvement. when it is a sitewide message or a group message, it makes a query and loads this info,
# so we have a message preview for everybody loaded on demand, instead of have the info duplicated for everybody
class Inbox(db.Model):
	recipient =  db.ReferenceProperty(User, collection_name='user_incoming_messages')
	remitent = db.ReferenceProperty(User, collection_name='user_sent_messages')
	message_id = db.ReferenceProperty(Message)
	date_sent = db.DateTimeProperty()
	subject = db.StringProperty()
	read = db.BooleanProperty(default = False)
	

	





