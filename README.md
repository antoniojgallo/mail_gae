#Mail

A mail application writen in python using GAE, Datastore and Flask

*NOTE: Mail is developed with the only aim to learn some technologies, and most probably doesn't make sense in real life. It does not have
anything to do with real email, it is just a centralized mail application*

Mail offers a RESTful api to interact with it. You can send messages to other users on the system, groups, clasrooms and also systemwide messages.
You can also read your mails, check your inbox and delete your messages. It has an autocomplete feature too

##Instalation

Create a Google App Engine instance. Change the `app.yaml` file to the data provided by your instance. Upload the code. Create a group
with the `group_name` field equal to `sitewide` (you can use for this the Google App Engine data viewer). Also create some users to play with

Now you should be ready to go.

##Usage

Mail exposes a RESTful API to use it. This aims to be a very small guide to use it

My app engine instance is called `secret-walker-332` (I promise Google offered me that name by default, I have nothing to do with that)
 so I will use that all the time. You just need to change this to your instance name

###Send mails

To send mails, make a POST request to [http://secret-walker-332.appspot.com/users/<int:user_id>/mail]

* `<int:user_id>` is the unique int value associated with the user that sends the email. It should be valid
* You can send mails to users or groups, but not both at the same time
* The body of the `content` cannot be an empty string
* The `subject` size cannot be larger than 100 characters


####If you are sending mails to another user
The body of the request must be a json like this

```
{
"subject":"This is a message to another user",
"content":"This is the content",
"recipient_id" : "5979693987659776"}

```
`recipient_id` must be a valid user id recipient for your mail

####If you are sending mails to group, class or sitewide
All the members of the group, class or the whole site will receive your message (if you are allowed)

The body of the request must be a json like this
```
{
"subject":"This is a message to a group, class o",
"content":"This is the content",
"group_id" : "5979693987659776"}

```

`group_id` must be a valid user id recipient for your mail. 

* If `group_id` is the id of a "regular" group (not class or systemwide), it will be sent only if your user has the group on its `groups` list
* If `group_id` is the id of the systemwide group, it will be sent only if your user has `is_administrator` flag as `True`
* If `group_id` is the id of a class group, it will be sent only if your user has the class on its `is_teacher_of` list

###Check your inbox
To check your inbox, make a GET request to [http://secret-walker-332.appspot.com/users/<int:user_id>/inbox?size=INT&offset=INT]

* `<int:user_id>` is the unique int value associated with the user that request the inbox. It should be valid
* `size` is the number of messages you want to get (starting from the newer ones). It is limited at 1000 messages
* `offset` is the number of messages you want to skip (starting from the newer ones)


You should get a JSON like this:

```
{
    "inbox_entries": [
        {
            "recipient_id": "5979693987659776",
            "remitent_id": "5979612987659776",
            "message_id": "5293323854020608",
            "date_sent": "2013-09-18T01:35:40.602531",
            "subject": "This is a message with content",
            "read": "True"
        },
        {
            "recipient_id": "5979693987659776",
            "remitent_id": "5979693987645776",
            "message_id": "5997011295797248",
            "date_sent": "2013-09-17T21:12:04.357435",
            "subject": "This is another message with content",
            "read": "False"
        },
        {
            "recipient_id": "5979693987659776",
            "remitent_id": "5979632987659776",
            "message_id": "6278486272507904",
            "date_sent": "2013-09-17T21:12:01.969089",
            "subject": "This is yet another message with content",
            "read": "False"
        }]
}
```

This JSON should be self-explanatory. It shows a preview of every message in the user's inbox ordered by date (newer messages first). In fact, shows all the data from the messages but the content. Every message has a `read` flag. That flag is set to `False` by default, and sets to `True` when you request the full version of that message (More about that later)


###Get a message
To get a message, make a GET request to [http://secret-walker-332.appspot.com/users/<int:user_id>/mail/<int:message_id>]
You can learn the id of the message from the inbox.
Once you request a message, it is automatically tagged as read

*`<int:user_id>` is the unique int value associated with the user that request the inbox. It should be valid and it should be the recipient of `<int:message_id>`. Remember that there could be multiple recipients per message (group messages)

You should get something like this
```
{
    "remitent": 5979693987659776,
    "date_sent": "2013-09-18T01:35:40.602531",
    "subject": "This is the last message with content",
    "content": "This is the content"
}
```

###Delete a message
To delete a message, make a DELETE request to [http://secret-walker-332.appspot.com/users/<int:user_id>/mail/<int:message_id>]

You can learn the id of the message from the inbox.

The message is deleted from the user inbox. If the only user that has that message on the inbox is the user that requests the message to
be deleted, the message is actually deleted. (That is, if it is a user to user message, or if the user is the only one that hasn't deleted
a group or sitewide message yet)

* `<int:user_id>` is the unique int value associated with the user that request the inbox. It should be valid and it should be a the recipient of `<int:message_id>`. Remember that there could be multiple recipients per message (group messages)

You should get something like this

```
{"result":"True"}
```

###Use the autocomplete feature

Mail API offers an autocomplete call for usernames. It gives you a list of usernames (up to 10) that matches the first characters of a username you are typing. Sadly, it is (still) case sensitive.

The implementation is a little bit tricky. Take a look at it if you are curious

To use it, make a GET request to [http://secret-walker-332.appspot.com/autocomplete?hint=STR]

* STR are the first characters of the user you are typing. It can be one character, two...

You should get something like this (being `STR=da` and the users shown, the only ones that whose prefix is `da`)

```
{
    "suggestions": [{
        "user_name": "daniel smith",
        "user_id": "6559961249218560"
    }, {
        "user_name": "daphne",
        "user_id": "4730373900599296"
    }, {
        "user_name": "david navarro",
        "user_id": "5979693987659776"
    }]
}
```

##Live demo. Use it right now!

I have created some users, groups and messages to let you play with the system that I have online at [http://secret-walker-332.appspot.com]

To make the API calls you can use `curl`. But I recommend [Rest console](https://chrome.google.com/webstore/detail/rest-console/cokgbflfommojglbmbpenpphppikmonn?hl=en) to try de application for a `man`-free experience (with `man` I mean the command, not anything related to gender)
Just remember when you put some JSON on the body of the call, to check the "application/json" box

###Users

* Daniel (username="daniel", user_id="123") is the system administrator of the site. He is also part of the "linux" group, and is teacher of "hackers hut" He takes lectures of "self driving cars"
* David (username="david", user_id="1234") is a student of "hackers hut". He is member of "mac lovers"
* James (username="james", user_id="1234") is a member of "linux" and teacher of "self driving cars"
* Laura (username="laura", user_id="1234") is a member of "mac lovers"


###Groups

* "sitewide" (group_name="sitewide", group_id="123") is the group all users are part of
* "hackers hut" (group_name="hackers hut", group_id="123") is a class
* "linux" (group_name="linux", group_id="123") is a group
* "mac lovers" (group_name="mac lovers", group_id="123") is a group
* "self driving cars"(group_name="self driving cars", group_id="123") is a class

##Files
* `datastore_model.py` is the datastore model for the app
* `app.yaml` is the information needed by GAE
* `mail.py` is where almost all the application logic is
* `main.py` its only job is mostly to call `mail.py`
* `mail_unit_test.py` is where the tests live
* I think that all the other things out there are mainly dependencies
