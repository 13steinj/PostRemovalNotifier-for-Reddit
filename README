The bot works in 3 parts. During the first 2 runs of the bot some initialization is needed. Comments might only be placed after the 3rd run.

In the first run of the bot, it stores the <GetNewPosts> most recent posts from <CurrentSubreddit>,  in the file <CurrentSubreddit>_posts_stored.txt

In the second run, that should start a few minutes later, it looks at which posts used to be in the <GetNewPosts> most recent posts,
but aren't any more, which are the removed posts. These removed posts are stored in the file <CurrentSubreddit>_posts_ToReply.txt
and then it also stores all the new posts like in run 1.
(The bot filters user-removed posts and shadowbanned users out during this step it also filters posts with a mod-reply. Users with low karma, <=10 combined, and accounts that are less than a week old are also filtered.)

In the third run, that should start again a few min later, it checks the comments in each of the posts that were stored in run 2 in CurrentSubreddit_posts_ToReply.
If the mods (or automoderator) removed a post but also left a comment, then there is no point in leaving a reply,
because the user already knows that their post is removed.
The delay between the 2nd and the 3rd run is to give the moderators some time if they plan to leave a written reaction to the post.
Posts that we have replied to are stored in: <CurrentSubreddit>_posts_Replied.txt


