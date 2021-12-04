# Update History

## v5.3.16

*Date: 2021/12/4*  
Feature Updates:  
1.Updated ICON  
2.Shortening .userctrl when window is too narrow  
3.Improved UI  
4.Added new share function which allows up to 20 shares for each book  
5.Added function at backend to remove HTML tags in string to prevent **XSS attack**  

Other Updates:  
1.Moved general js code in html files to general.js  
2.Updated footer (User privacy is still valued, no cookie is used and all data are still stored in local storage)  

Bug Fixes:  
1.Fixed some bugs on /user by separating user pages to multiple files  

## v5.3.15

*Date: 2021/11/28*  
Feature Updates:
1.Added transition for rect:hover  
2.Removed unnecessary columns on /discovery table  
3.Added privilege display on /admin/userlist  
4.Allowed email sign in  

Bug Fixes:  
1.Fixed some bugs on /user frontend page  
2.Fixed the bug that banned user could still appear on public pages  
3.Fixed the bug that username couldn't be parsed correctly on /user if user doesn't have name tag  

## v5.3.14

*Date: 2021/11/27*  
Feature Updates:  
Updated UI  

## v5.3.13

*Date: 2021/11/27*  
Feature Updates:  
1.Moved detailed user session info to modal, displaying only basic info on page  
2.Merged some database tables  
3.Improved database operation by converting multi-row id info to single-row id string (somehow compressing the database)  
4.Allowed admins to use username for userId in CLI commands  
5.Allowed admins to revoke user creation in 2 hours after the user is created by using the delete_user command  
6.Removed modal from html files and they will be loaded by javascript  

Bug Fixes:  
1.Changed bar chart ratio to 0.8  
2.Updated max length in database  
3.Fixed the bug that users are not logged out completely when session expired  
4.Fixed the bug allowing users to set negative integars for goal  

## v5.3.12

*Date: 2021/11/21*  
Bug Fixes

## v5.3.11  

*Date: 2021/11/21*  
Feature Updates:  
1.Added mute / unmute functions for admins to manage whether a user is allowed to post in Discovery  
2.Added Goal & CheckIn function to stimulate users to continue memorizing  
3.Challenge YESNO is no longer considered as a Challenge Mode.  
  Challenge YESNO is renamed to Practice, the old Practice Mode is renamed to Switch (users are switching the question & answer only).  
  Challenge CHOICE is the only Challenge Mode and it is renamed to Challenge.  
  Please note that the backend mechanism (different question & answer display rate) of the new Practice Mode is the same as the original Challenge YESNO. But it will not update challenge record.  

## v5.3.10

*Date: 2021/11/21*  
Feature Updates:  
1.Added visualized statistics for books  
2.Improved chart animation  
3.Added Notification function to display user events  

## v5.3.9

*Date: 2021/11/20*  
Bug Fixes:  
1.Fixed a bug with user login  
2.Fixed the bug that public user profile cannot be shown correctly  

Feature Updates:  
1.Combined error pages to one page  
2.Updated ICON  

## v5.3.8

*Date: 2021/11/20*  
Feature Update:  
Visualized user data  

## v5.3.7

*Date: 2021/11/19*  
Bug Fixes:
1.Fixed the bug that username on title cannot be displayed  

Feature Updates:  
1.Moved admin page entry to left-side navigation bar  
2.Replaced admin restart server button for an admin command  

## v5.3.6

*Date: 2021/11/19*  
Bug Fixes:  
1.Added function to check input length before updating database  
2.Discovery requests will show r.msg when r.success = False  
3.Fixed the bug that admin user list cannot be shown (500)  
4.Fixed the bug that #navusername does not display sometimes  
5.Fixed the bug that showing unavailable discovery posts in discovery list  

Feature Updates:
1.Made username the same color as name tag  
2.Added statistics display operation in question list  
3.Improved Challenge CHOICE UI  
4.Added sound response for Challenge CHOICE  
5.Updated password trial limit to limit login attempts per ip  
6.Added custom 4xx 5xx error pages  
7.Improved book list UI  
8.Added top post for Discovery  

## v5.3.5  

*Date: 2021/11/14*  
1.Added name tag, which will be shown beside the user's username, as a representative of the user  
  Name tag can only be added by admins  
2.Added hyberlink to user profile for all username displayed on the page  

## v5.3.4  

*Date: 2021/11/14*  
Added Challenge CHOICE to make it like a quiz  
The old challenge mode is renamed to Challenge YESNO  

## v5.3.3  

*Date: 2021/11/13*  
Bug Fixes:  
1.Fixed the bug that some Noty Notifications are not displaying correctly  
2.Fixed the bug that admins / publishers cannot delete discovery post at /discovery (redirecting too fast)  
3.Fixed a bug that sessions don't expire when users sign out manually  

Feature Updates:  
1.Added Ctrl+Enter as shortcut to submit modal with textarea  
2.Added function to show discovery post with import count / member count  
3.Added function for admins to pin discovery posts  
4.Added settings sync, user can decide when to upload / download settings  
  When user logins using a new device, the settings will be downloaded automatically  

## v5.3.2  

*Date: 2021/11/13*  
Bug Fixes:  
1.Fixed the issue that MySQL connection often disconnects (by updating the connection before query)  

Feature Updates:  
1.Added function to automatically block logins of default user when a user (uid: 1) is created  
2.Encoding username in database to allow more characters in username  
3.Added book button hover for book.html  
4.Added operation column for question list with operations: edit, delete (from book)  
5.Added operation column for group member list with operations: kick, (undo) make editor  
6.Added a loading spinner at top-left cornor of page when there are active (pending) ajax request(s)  
7.Added session management function where users can view all active sessions  

## v5.3.1

*Date: 2021/11/13*  
Added support for MySQL database  

## v5.2.5

*Date: 2021/11/12*  
Bug Fixes:
1.Fixed the bug that question not displaying in challenge mode with settings.swap = 1 (display answer mode).  
2.When showing / hiding modal, no longer using toggle and changed to use show / hide directly to prevent abnormal behaviour.  
3.Made all ajax requests with async enabled.  
4.Fixed the bug that tables are having dark background while in light mode.  

Feature Updates:  
1.Allowed users to click row to show Discovery post without pressing the Show operation.  
Hiding operation column for users and only display delete operation for admins.  
2.Move functions that are used by nearly all pages to a separate general.js and each page will import it.  
3.Added sync button for book page.  
4.Added front-end notifications for request errors.  
5.Add book list preview for all pages.  

## v5.2.4

*Date: 2021/11/7*  
Added group anonymous function supporting Open, Anonymous and Full Anonymous

## v5.2.3

*Date: 2021/11/7*  
Added function for admins to manage discovery post  

## v5.2.2

*Date: 2021/11/7*  
Added Discovery for Group  

## v5.2.1

*Date: 2021/11/6*  
1.Introduced Discovery! Users can find books shared with public by other users.  
2.Updated account deletion mechanism. This will only remove the user's sensitive data, all his / her other data such as questions and books will be preserved. This update is to adapt the Discovery function so that data from deleted users can also be found.  
Note: Users can always delete their other data include questions and books manually before deletion. And users can request a complete data deletion by providing their UID with admin.  

## v5.1.5

*Date: 2021/11/6*  
1.Added function for user to press enter to submit modal form  
2.Added refresh button for user to update data without refreshing the page  
3.Added UI for admin cli  
4.Added user list table for admin  
5.Made table rows colorful  
6.Added login protection to prevent brute force password attack  
7.Moved in-memory variables to database for better mutli-threading (gunicorn)  

## v5.1.4  

*Date: 2021/11/6*  
1.Added a separate page for "books" (Support slide-out in home page + a dedicate page for it)  
2.Updated UI  
3.Added Dark Mode  
4.Added function to read answer by double-clicking it  

## v5.1.3

*Date: 2021/11/5*  
Project renamed again, to "My Memo" now  
Why renaming?  
I have found that the functions of my project is not limited only to "word memorizing", based on my own using experience, it can be used to memorize anything I want, e.g. math formula, chinese poems.  
I think renaming it will make the use of my project wider.  

## v5.1.2

*Date: 2021/11/5*  
Fixed some bugs  
1.Fixed the bug that non-group-owner can see the management buttons on group member page  
2.Disallowed user to join a group for multiple times  
3.Fixed incorrect word id update  
4.Fixed incorrect group member progress display  
5.Disabled word reading when they are invisible  
6.Fixed the bug that word id cannot be found when word book is specified and there are multiple words in database  

## v5.1.1

*Date: 2021/10/30*  
Brand new website!  
Frontend rebuilt using bootstrap, abandoning canvas  

## v4.1.3

*Date: 2021/10/29*  
1.Modulize server side file structure  
Move all templates & static files to frontend folder which will be handled by nginx directly  
Backend server will only handle api requests  
2.Updated import & export function:  
Raw database will be converted to Excel .xlsx file  
Import & export cache will be kept in memory  
3.Fixed a bug of challenge mode causing bad randomness  

## v4.1.2

*Date: 2021/10/24*  
Added Group member list & management  
Added word book progress monitor  

## v4.1.1

*Date: 2021/10/23*  
Added "Group" to enable word book sync & member progress sharing  
Currently only basic functions & word book sync are done  
Owner is allowed to revoke group code / make group private  

## v3.3.2

*Date: 2021/10/16*  
Better word list display & operation  
Allowed user to add / import word(s) directly to word book  

## v3.3.1

*Date: 2021/10/9*  
Added admin cli control panel  
Added privilege system to expand word limit for specific users  

## v3.2.1

*Date: 2021/10/6*  
Added sharable word book  
Added function to rename word book

*Date: 2021/10/9*  
Added config file  
Added user & word limit  

## v3.1.3

*Date: 2021/10/5*  
Added function to edit words by double-clicking the word (available at word list & memorizing page)  
Added keyboard control

## v3.1.2

*Date: 2021/10/5*  
Added function to import to replace only conflicted words (overwrite mode)
Added select-all & deselect-all options for word list

## v3.1.1

*Date: 2021/10/5*  
Added full-featured word book function (include create / delete / edit / select)  
**As word book function comes out, the version is upgraded to v3**

## v2.1.3

*Date: 2021/10/4*  
Added function to edit word status in batch in word list table

## v2.1.2

*Date: 2021/10/3*  
Improved UI (removed backend split line, frontend will calculate where to split line automatically)  
Added word book display function, to prepare for full-featured word book function

## v2.1.1

*Date: 2021/10/3*  
Added offline mode which use local word list  
(No tagging / deleting allowed in offline mode)
In offline mode, user can use the website without logging in  

Added an admin option to restart backend program + a reverse proxy (authentication) protected endpoint for restarting backend program  

## v2.0.4

*Date: 2021/10/2*  
Improved UI & Mobile Usability  
Less server load: screensaver get word from local list

## v2.0.3

*Date: 2021/09/25*  
Added frontend word list

## v2.0.2

*Date: 2021/09/24*  
Update user session backend code  
**Changed project name to "Word Memo" (The original name is "Word Memorizer")**

## v2.0.1

*Date: 2021/09/20*  
Added basic user authorization system  
Added more functions to user system  
**As user system comes out, the version is upgraded to v2**

-----

## v1.0.5

*Date: 2021/09/20*  
Added challenge mode  
Added word statistics  
Added "Add single word" function

## v1.0.4

*Date: 2021/09/19*  
Change backend data structure (from .xlsx table) to sqlite database  
Update frontend page

## v1.0.3

*Date: 2021/04/09*  
Update tag & remove mechanism  
Rebuild data processing mechanism  
Minor optimization  
Added download function  
Add pausing & playing for autoplayer

## v1.0.2

*Date: 2021/03/26*  
Added word list data uploader at client side  
Added change password function client side  
Added auto player  
Updated homepage

## v1.0.1

*Date: 2021/02/07*  
Fixed some minor bugs & improved loading speed

## v1.0.0

*Date: 2021/01/31*  
Initial commit  
**The start of this project**
