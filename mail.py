from flask import Flask, jsonify, request, make_response, url_for, make_response
from flask.views import MethodView
from flask.ext.restful import Api, Resource, reqparse, fields, marshal, abort
from datastore_model import *
from google.appengine.ext import db
import datetime
import logging
import json

app = Flask(__name__)
api = Api(app)


def abort_if_entity_not_exists(kind, entity_id):
	entity = db.get(db.Key.from_path(kind, entity_id))
	if entity:
		return entity
	else:		
		abort(404, message="The identifier for the resource " + kind + " is not valid")
		
#This class populates the datastore with some data for testing. Groups and users
class Populate(Resource):
	def get(self):
		sitewide = Group(group_name="sitewide", is_classroom=False)
		sitewide.put()

		hackers = Group(group_name="hackers hut", is_classroom=True)
		hackers.put()

		linux = Group(group_name="linux", is_classroom=False)
		linux.put()

		mac = Group(group_name="mac lovers", is_classroom=False)
		mac.put()

		cars = Group(group_name="self driving cars", is_classroom=True)
		cars.put()

		daniel = User(user_name="daniel", is_administrator=True, groups=[linux.key(),hackers.key(),cars.key()], is_teacher_of=[hackers.key()])
		daniel.put()

		david = User(user_name="david")
		david.groups=[hackers.key(),mac.key()]
		david.put()

		james = User(user_name="james")
		james.groups=[linux.key(),cars.key()]
		james.is_teacher_of=[cars.key()]
		james.put()

		laura = User(user_name="laura")
		laura.groups=[mac.key()]
		laura.put()

		return {'result': True }

api.add_resource(Populate, '/populate')	


class AutocompleteAPI(Resource):


#Autocomplete call. It is case sensitive
	def get(self):	

		parser = reqparse.RequestParser()
		parser.add_argument('hint', type = str, required = True, help = 'No hint provided', location='args')
		args = parser.parse_args()
		hint_args = args['hint']

		q = db.GqlQuery("SELECT * FROM User WHERE user_name >= :1 AND user_name < :2",hint_args, unicode(hint_args) + u"\ufffd") 

		results = q.fetch(10)

		response = '{"suggestions":['

		inside_loop = False

		for suggestion in results:
			response = response + '{"user_name":"' + suggestion.user_name +'","user_id":"'+str(suggestion.key().id())+'"},'
			inside_loop = True		

		if inside_loop:
			response = response[:-1]

		response = response + ']}'

		formated_response = make_response(response,200)
		
		formated_response.headers['content-type'] = 'application/json'

		return formated_response



api.add_resource(AutocompleteAPI, '/autocomplete', endpoint = 'autocomplete')




class InboxAPI(Resource):


#Get the first n message previews of the user to build the inbox. In the query are the number of messages needed and the offset
#Note that this does not retrieve full messages, but only their "preview"
	def get(self, user_id):	

		parser = reqparse.RequestParser()

		parser.add_argument('offset', type = int, required = True, help = 'No offset provided', location='args')
		parser.add_argument('size', type = int, required = True, help = 'No size provided', location='args')

		args = parser.parse_args()

		arg_offset = args['offset']

		size = args['size']

		user = abort_if_entity_not_exists('User', user_id)

		q = db.Query(Inbox).filter('recipient =', user).order('-date_sent')
		results = q.fetch(size, offset = arg_offset)

		response = '{"inbox_entries": ['

		inside_loop = False

		for inbox_entry in results:
			response = response + '{"recipient_id":"' + str(user_id) + '", "remitent_id":"' + str(inbox_entry.remitent.key().id())  +'", "message_id":"'+ str(inbox_entry.message_id.key().id())+ '", "date_sent" :"' + inbox_entry.date_sent.isoformat() + '", "subject":"' + inbox_entry.subject +'", "read":"' + str(inbox_entry.read) + '"},'
			inside_loop = True

		if inside_loop:
			response = response[:-1]
						
		response = response + ']}'
				
		formated_response = make_response(response,200)
		
		formated_response.headers['content-type'] = 'application/json'

		return formated_response

			

api.add_resource(InboxAPI, '/users/<int:user_id>/inbox')



#Get an specific message, or delete it
class MessageAPI(Resource):


	def get(self, user_id, message_id):

		#Check that the user has that message in his inbox (has permission to see it)



		inbox_query = db.Query(Inbox).filter('message_id =',  db.Key.from_path('Message', message_id)).filter('recipient =',  db.Key.from_path('User', user_id))

		message_inbox = inbox_query.get()

		if message_inbox:

			#If he does, mark the message as read in his inbox 

			inbox_message = inbox_query.get();

			inbox_message.read = True

			inbox_message.put()
	
			#and return the json with the message		

			message = Message.get(db.Key.from_path('Message', message_id))
			content = message.content

			message_render = {
		          'remitent': message.remitent.key().id(),
		          'date_sent': message.date_sent.isoformat(),
		          'subject': message.subject,
		          'content': content.encode(),
		      }

			return message_render

		else:	
			abort(403, message="The combination of user and message is not valid")



	def delete(self, user_id, message_id):

		#Check that the user has that message in his inbox (has permission to see it)
		inbox_query = db.Query(Inbox).filter('message_id =',  db.Key.from_path('Message', message_id)).filter('recipient =',  db.Key.from_path('User', user_id))


		message_inbox = inbox_query.get()


		if message_inbox:
			
			message = Message.get(db.Key.from_path('Message', message_id))
	

		  #If it's not a group message, I delete the actual message. If it's a group message, but only
			#this user has it in the inbox, I delete it as well
		
			size = len(db.Query(Inbox).filter('message_id =',  db.Key.from_path('Message', message_id)).fetch(2))

			unique = (size == 1)

			if ( (message.group is None) or not hasattr(message, 'group')) or unique:
				message.delete()

			#And then I delete the preview from the inbox (For all cases)
			message_inbox.delete()

			return {'result': True }


		else:
			abort(403, message="The combination of user and message is not valid")

api.add_resource(MessageAPI, '/users/<int:user_id>/mail/<int:message_id>', endpoint = 'message')


#Sends a new message, to a user or a group THE CONTENT CANNOT BE AN EMPTY STRING. check also
#the possible combinations between empty group, empty recipient, empty stirng for group,
#empty list for recipient
#also check restrictions of subject (size of string<500), etc

class SendMailAPI(Resource):
#comprobar el caso especial en el q group_id o user_id no sean none, pero su valor sea un string vacio

	def post(self, user_id):

		parser = reqparse.RequestParser()

		parser.add_argument('subject', type = str, required = True, help = 'No subject provided', location = 'json')
		parser.add_argument('content', type = str, required = True, help = 'No content provided', location = 'json')
		parser.add_argument('group_id', type = int, required = False, location = 'json')
		parser.add_argument('recipient_id', type = int, required = False, location = 'json')

		#I need to check for the correct format on the request
		args = parser.parse_args()

		user = abort_if_entity_not_exists('User',user_id)

		if len(args['content'])<1:
			abort(400, message="The content of the message cannot be empty")		

		if len(args['subject'])>100:
			abort(400, message="Subject size cannot be greater than 100 characters")		

		#It is posssible to send messages to groups or users, but not both		
		if (args['recipient_id'] is not None ) and (args['group_id'] is not None): 
			abort(400, message="You can send a message either to a group or a user, but not both at the same time")

		#We create the message..
		
		date = datetime.datetime.now()

			
		message = Message(remitent = user, subject = args['subject'], date_sent = date, content = db.Text(args['content']) )

				
		#If it's a group or sitewide message
		if args['group_id'] is not None:
			group = abort_if_entity_not_exists('Group',args['group_id'])
			#Only administrators are allowed to send sitewide messages
			if (((group.group_name == 'sitewide') and (user.is_administrator) ) or
			#Only teachers of a classroom are allowed to send classroom wide messages to their clasrooms
				(( (group.is_classroom) and (group.key() in user.is_teacher_of) ) and (group.key() in user.groups) )or
			#Only users who are member of a group are allowed to send messages to that group
				((group.key() in user.groups) and not group.is_classroom) ):
				#put the message on the system
				message.group=group
				message.put()
				if group.group_name == 'sitewide':
					#Let's add an entry in the inbox per user. I know it's expensive but.. POSSIBLE BOTTLENECK
					for dest in db.Query(User):
						Inbox(recipient = dest.key(), remitent = user, message_id = message, subject = args['subject'], date_sent = date ).put()
				else:
					for dest in group.members:
						Inbox(recipient = dest.key(), remitent = user, message_id = message, subject = args['subject'], date_sent = date ).put()
				
			else:
				abort(403, message="You do not have permission to send that message")

		if args['recipient_id'] is not None:
			#Let's put the message on the system
			message.put()			
			#And in the recipient_id inbox
			Inbox(recipient = abort_if_entity_not_exists('User',args['recipient_id']), remitent = user, message_id = message, subject = args['subject'], date_sent = date).put()
		
		return {'result': True }		
			

api.add_resource(SendMailAPI, '/users/<int:user_id>/mail')




