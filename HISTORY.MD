# Update History

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
Added previlege system to expand word limit for specific users  

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
