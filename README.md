# My Memo
*A light-weight memo website made with python flask + html5 bootstrap.*  
[Website](https://memo.charles14.xyz/)

*It's only tested in python3.8 + Chrome / Firefox browser environment. But it should support python3.\* and most browsers.*

*All the commits since [c610d51](https://github.com/Charles-1414/MyMemo/commit/c610d51cc357b7f0841de62ff77157f93ed986fa) should be signed with my GPG key and marked as verified. Otherwise it might be committed by an unknown person. Commit [99efec8](https://github.com/Charles-1414/MyMemo/commit/99efec8dc9d3e4976c61f17764869a84df50722e) is unverified because the email was configured incorrectly.*

Current version: v5.3.11  

## About v5  

My Memo v5 is built with python flask + html5 bootstrap.  
We have a brand new UI comparing to the older versions using canvas.  

Switch? Practice? Challenge?  
The old Challenge CHOICE has been renamed to Challenge and it's the only challenge mode that will update challenge record.  
The old Challenge YESNO has been renamed to Practice. It will display specific questions & answers based on an algorithm that is the same as challenge mode.  
The old Practice has been renamed to Switch, as users just switch between questions & answers.  

Discovery, the first community function, has been introduced!  
You can post your shared books and public groups to Discovery!  
Admins are able to delete / update post to prevent abuse.  

MySQL, a popular database for websites, is finally implemented!  
You can decide whether to use MySQL or continue to use sqlite by changing the config.  

Please note that the first user registered (besides default user) will be given admin permission automatically, and when it's registered, the default user will be disabled.  

## About My Memo

You have four modes to start the site: Switch, Practice, Challenge, Offline.  
You can use Switch to switch between questions easily and it should be used for first-time memorizing.  
You need to answer whether you remember the answer in Practice so it should be used for second-time memorizing.  
To test whether you have memorized the answers, use Challenge mode to do some quizzes.  
Offline Mode? It isn't completely offline. But your device will not communicate with the server as the words are backed up locally.  

Books are supported! You can create unlimited books (this can be limited in config.json at backend) and add any questions to it! Select a book before starting memorizing or the default (All questions) will be applied.

Groups are also supported! You can learn with your friends using group. The questions & answers will be synced automatically when any update is made. Also, you will be able to see your friends' progress!  
(Whether you have memorized the item is based on the passed challenges of it, once you have passed 2 challenges in a row, the item will be regarded as memorized)  

All users have their rights to download their data stored on the server or delete their account and wipe their data permanently.  

## About the demo

New users can only be invited by old users to prevent abuse, so they must enter an invitation code when registering. (You can allow any user to register by changing the config)  

I'm hosting it on my own server and you can press [this link](https://memo.charles14.xyz/) to get there.  
The website is archived by Wayback Machine for future offline functions (And if my server is offline, CloudFlare will display that archive)

## More Info

Please open an issue if you met any bugs during the use.  
You could also open an issue for good suggestions and I'll decide whether to add it.  
**This product can also be used to memorize any other thing such as formulas in Math!**

## License

**GNU General Public License is used for this project. You must open source your project and let me know about it if your code is based on my code. Otherwise you will be held legally responsible!**
