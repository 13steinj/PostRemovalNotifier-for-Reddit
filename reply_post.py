#!/usr/bin/python
import praw
import os
import datetime
from config_bot import *

# Please send /u/ERIKER1 a message on reddit when you are planning to use (parts of) this code.

# Praw 3.5 and Python 2.7 were used.
#
# The bot works in 3 parts. The first part stores posts from the new queue.
# The second part two part selects posts that need a reply
# The third part (which is located in the code between the first and second parts) leaves a reply if there hasn't been a reply from a moderator.
#
# In the first part, it stores the <GetNewPosts> most recent posts from the new queue from <CurrentSubreddit> in the file <CurrentSubreddit>_posts_stored.txt
#
# In the second part, that should start a few minutes later, it looks at which posts used to be in the <GetNewPosts> most recent posts,
# but aren't any more, which are the removed posts. These removed posts are stored in the file <CurrentSubreddit>_posts_ToReply.txt
# and then it also stores all the new posts like in run 1.
# (The bot filters user-removed posts and shadowbanned users out during this step it also filters posts with a mod-reply. Users with low karma, <=10 combined, and accounts that are less than a week old are also filtered.)
#
# In the third part, that should start again a few min later, it checks the comments in each of the posts that were stored in run 2 in CurrentSubreddit_posts_ToReply.
# If the mods (or automoderator) removed a post but also left a comment, then there is no point in leaving a reply,
# because the user already knows that their post is removed.
# The delay between the 2nd and the 3rd run is to give the moderators some time if they plan to leave a written reaction to the post.
# Posts that we have replied to are stored in: <CurrentSubreddit>_posts_Replied.txt
#
# In my current implementation I let the bot run every 3 minutes.
# I recommend using the following guide for running it automatically: http://pythonforengineers.com/build-a-reddit-bot-part-3-automate-your-bot/

# Variables for easy configuration:

# The following variables are included to prevent that the bot will reply to spam.
# A possible additional anti-spam variable (for example the amount of karma on a post) could also be included.
# If CombinedKarma and AccountAge are set to zero, then it might be worthwhile to remove certain lines to reduce the # of requests.

CombinedKarma = 10 #Combined karma that a user needs before we will reply to them.
AccountAge = 7 #Account age that a users needs. Age is in days
GetNewPosts = 300 # Number of posts that are monitored (Sends reddit an extra request per 100 requested posts, max 900, 1000 gives some issues)

# Check that the file that contains login details exists
if not os.path.isfile("config_bot.py"):
    print "You must create a config file with your username and password."
    print "Please see config_bot.py"
    exit(1)

# I kept the following variables in the above config file.
# REDDIT_USERNAME =
# REDDIT_PASS =
# VersionNumber =
# USER_AGENT =   #Could depend on version number.

# Only needed for Oauth login (see some praw Oauth guides for this)
#REDDIT_SECRET=
#REDDIT_ID =
#refresh_token =


#Simple login (eliminates need of Oauth login)
r = praw.Reddit(user_agent=USER_AGENT)
r.login(REDDIT_USERNAME, REDDIT_PASS)



#Oauth Login (partially, read some guide on it. Make sure to also register the bot according to the rules and obtain the Bot ID and Bot secret.):
# r = praw.Reddit(user_agent=USER_AGENT)
# r.set_oauth_app_info(REDDIT_ID, REDDIT_SECRET, redirect_uri='http://127.0.0.1:65010/authorize_callback')


#Only needed for the first run of the bot
# url = r.get_authorize_url('uniqueKey', 'edit flair history identity modconfig modcontributors modflair modlog modothers modposts modself modwiki mysubreddits privatemessages read report save submit subscribe vote wikiedit wikiread', True)
# import webbrowser
# webbrowser.open(url)

#Running the above lines will send you to a page where you should copy the end of the url.
#print r.get_access_information("END OF URL")
#This will give you a refresh code that you should specify on the above part.


# Continuation of the Oauth login.
# r.refresh_access_information(refresh_token)
# r.config.api_request_delay = 1 #This will increase the number of requests to one per second (only allowed if you use Oauth)

#Shows some extra details, remove or set to 0 for no details.
r.config.log_requests=2

# Load list of whitelisted subreddits.
if not os.path.isfile("ListOfSubreddits.txt"):
    print "Please create a file named ListOfSubreddits.txt and add here the subreddit(s) that you want to monitor."
    exit(1)

# If we have run the code before, load the list of posts we have replied to
else:
    # Read the file into a list and remove any empty values
    with open("ListOfSubreddits.txt", "r") as f:
        ListOfSubreddits = f.read()
        ListOfSubreddits = ListOfSubreddits.split("\n")
        ListOfSubreddits= filter(None, ListOfSubreddits)

# For loop over all the subreddits in the list.
for CurrentSubreddit in ListOfSubreddits:

    # Have we run this code before? If not, create some empty lists
    if not os.path.isfile(CurrentSubreddit +"_posts_stored.txt") or not os.path.isfile(CurrentSubreddit +"_posts_Replied.txt") or not os.path.isfile(CurrentSubreddit +"_posts_ToReply.txt"):
        posts_stored = []
        posts_Replied = []
        posts_ToReply = []
        new_posts_ToReply = []


    # If we have run the code before, load the files with the information from the other runs.
    else:
        # Read the file into a list and remove any empty values
        with open(CurrentSubreddit +"_posts_stored.txt", "r") as f:
            posts_stored = f.read()
            posts_stored = posts_stored.split("\n")
            posts_stored = filter(None, posts_stored)


        with open(CurrentSubreddit +"_posts_Replied.txt", "r") as f:
            posts_Replied = f.read()
            posts_Replied = posts_Replied.split("\n")
            posts_Replied = filter(None, posts_Replied)

        with open(CurrentSubreddit +"_posts_ToReply.txt", "r") as f:
            posts_ToReply = f.read()
            posts_ToReply = posts_ToReply.split("\n")
            posts_ToReply = filter(None, posts_ToReply)
            new_posts_ToReply = []


    #PART 1 STARTS HERE. Store posts from the new-queue
    # Get the newest <GetNewPosts> posts from our subreddit
    subreddit = r.get_subreddit(CurrentSubreddit)
    NewPosts = subreddit.get_new(limit=GetNewPosts)
    submissions_list = [x.id for x in NewPosts]

    # Remove the last posts from posts_stored to prevent that they get marked as removed if they get pushed out of submissions_list by new posts.
    for submission in submissions_list:
        if submission not in posts_stored and len(posts_stored) > 0:
            del posts_stored[-1]

    # PART 1 ENDS HERE


    # PART 3 STARTS HERE. This is the part where we leave a comment.
    #Get list of moderators
    moderators = r.get_moderators(CurrentSubreddit)

    for post_id in posts_ToReply:
        #Get the posts that we considered for removal in Part 2
        submission = r.get_submission(submission_id=post_id, comment_limit=50, comment_sort='new')
        NewComments = submission.comments

        # Delete needed to ignore nested comments.
        if len(NewComments) > 0 and NewComments[-1].__class__.__name__ is not 'Comment':
            del NewComments[-1]

        #find all recent (top level) authors and check if they are mods. If they are not, leave comment.
        #We need to do this check again, because mods might have left a reply between the run of Part 2 and Part 3.
        AllNewAuthors = [comments.author for comments in NewComments]
        a = [str(author) for author in AllNewAuthors]
        b = [str(mods) for mods in moderators]
        ModsInComment = list(set(a) & set(b))

        if len(ModsInComment) is 0:
            # Reddit has some restrictions on the number of posts/comments that an account can make. This try catches this if it is not possible to reply.
            try:
                submission.add_comment(
                    "This post has been removed **by the moderators of this subreddit**, ***[not me]***. I am just a nice bot that notifies people if the moderators weren't able to do so.  \n" +
                    "By the way that reddit works, this is not directly visible to you, but if you [check the new-queue of " +
                    CurrentSubreddit + "](http://www.reddit.com/r/" + CurrentSubreddit +  "/new/) then you can see that your post doesn't show up there.   \n"
                    "If you want to know why your post was removed, you should first check all the rules of this subreddit. These rules can generally be found in the sidebar of the subreddit. " +
                    "Posts also commonly get removed by the moderators if the quality of the post is deemed too low by the moderators or if there have been too many similar posts.   \n" +
                    "In some subreddits, a removal reason will only be left in a flair. This flair is on the right or left of the title of your post. \n\n"
                    "If, after reading the rules, you still don't know why your post was removed then you could consider [sending a message to the moderators of the subreddit.]" +
                    "(https://www.reddit.com/message/compose?to=" + CurrentSubreddit + "&subject=Removed%20post&message=Dear%20moderators,%20I%20just%20noticed%20that%20my%20post%20was%20removed.%20I%20checked%20the%20rules%20and%20I%20am%20not%20sure%20why%20it%20was%20removed.%20Could%20you%20please%20give%20me%20an%20explanation?%20https://www.reddit.com/r/"
                    + CurrentSubreddit + "/comments/" + post_id + ") \n \n--- \n \n" +
                    "^[FAQ](http://www.reddit.com/r/PostRemovalNotifier/wiki/index) ^| [^Subreddit ^of ^bot](http://www.reddit.com/r/PostRemovalNotifier/) ^| [^(Post not removed or other issue?)](http://www.reddit.com/r/PostRemovalNotifier/submit?selftext=true&title=[ISSUE]%20in%20" +
                    CurrentSubreddit + "%20&text=There%20was%20an%20issue%20with%20the%20bot%20in%20the%20following%20post.%20Please%20investigate.%20https://www.reddit.com/r/"
                    + CurrentSubreddit + "/comments/" + post_id + " %20<Enter%20further%20details%20here>.) ^| ^by ^/u/ERIKER1 ^| [^(Source)](https://github.com/ERIKER1/PostRemovalNotifier-for-Reddit) \n \n ^^Version ^^" + VersionNumber +
                    " ^^-- ^^I ^^am ^^still ^^a ^^very ^^new ^^bot, ^^which ^^means ^^that ^^reddit ^^limits ^^me ^^a ^^lot. ^^Please ^^give ^^me ^^some ^^love ^^so ^^that ^^I ^^can ^^work ^^even ^^harder.")
                posts_Replied.append(post_id) #Store the posts we replied to.
            except:
                print "error couldn't make a post, probably 10 min rule"
                pass

    #PART 3 ENDS HERE

    #PART 2 STARTS HERE (check which posts have been removed by the mods and check if the user has sufficient karma.)

    SubredditComment = 1 #stop commenting in a subreddit after a single comment. Speeds up the code when the karma of the bot is too low. Remove later.
    for post_id in posts_stored:

        # if we did see the post before, but not anymore and if we didn't reply already
        if post_id not in submissions_list and post_id not in posts_Replied and SubredditComment:

            #Get the post that was removed from the new queue (by either a mod or the user, user-removed posts are filtered later)
            submission = r.get_submission(submission_id=post_id,comment_limit=50 ,comment_sort='new')
            NewComments = submission.comments

            # Delete needed to ignore nested comments.
            if  len(NewComments) > 0 and NewComments[-1].__class__.__name__ is not  'Comment':
                del NewComments[-1]

            #Added a try in case the user got shadowbanned.
            try:

                # Do not reply if user deleted his own post.
                # and do not reply if the author has a combined karma less than <CombinedKarma>
                # and do not reply if the author has an account that is younger than <AccountAge>
                if submission.author is not None and submission.author.link_karma + submission.author.comment_karma > CombinedKarma and\
                datetime.datetime.now() - datetime.datetime.fromtimestamp(submission.author.created_utc) > datetime.timedelta(days=AccountAge):
                    SubredditComment = 0 #stop commenting in a subreddit after a single comment. Speeds up the code when the karma of the bot is too low. Remove later.

                    # find all recent (top level) authors and check if they are mods. If they are not, add this post to the post that we have to reply to.
                    AllNewAuthors = [comments.author for comments in NewComments]
                    a = [str(author) for author in AllNewAuthors]
                    b = [str(mods) for mods in moderators]
                    b.append('AutoModerator') # Adds automoderator (needed for subreddits that use the automod, but that don't have it in their mod list)
                    ModsInComment = list(set(a) & set(b))
                    if len(ModsInComment) is 0:
                        new_posts_ToReply.append(post_id) #Consider replying to this post the next time we run the program. Needed for PART 3.

            except:
                print "error couldn't get user, user was probably shadowbanned."
                pass

    # PART 2 ENDS HERE

    # Write our updated lists back to the files
    with open(CurrentSubreddit +"_posts_stored.txt", "w") as f:
        for post_id in submissions_list:
            f.write(post_id + "\n")

    with open(CurrentSubreddit +"_posts_ToReply.txt", "w") as f:
        for post_id in new_posts_ToReply:
            f.write(post_id + "\n")

    with open(CurrentSubreddit +"_posts_Replied.txt", "w") as f:
        for post_id in posts_Replied:
            #f.write("http://www.reddit.com/" + post_id + "\n")
            f.write(post_id + "\n")



