# My Memo

**A light weight memo website based on Python FastAPI + HTML5 Bootstrap.**  
**Version: v5.6.12**  
*The author has finished the development on this project. Only bug fixes will be applied and no more new functions will be added.*  
*You are welcomed to contribute to this project by helping to do bug fixes and add new features. Pull requests will be reviewed at weekends.*  

---

## Highlights

**3 Modes** - *Switch, Practice and Challenge*  
**Book** - *To better organize your questions*  
**Group** - *To sync book data & progress among group members*  
**Discovery** - *A community function to share book with public*  
**Users** - *Support multiple users and user security & management functions, and instant data export!*  

---

## Background

*It's a story about why this project started and how it developed, written on Dec 9th, 2021.*  
On a night in Janurary 2021, when I was in Grade 9, trying hard to memorize the words of the university entrance exam (yes, I already started that when I was in junior middle school, as those words are examined in the tests of high school pre-accept exams), I found it hard not to look at the words when looking at the definitions, my eyes just glimpse at the answers subconsciously although I don't want to do so. Also, I found it difficult to manage the words that I already memorized, and those need more practice. Hence, I created My Memo v1 (It was called Word Memorizer at that time). It only supported tagging & deleting words, importing with Excel table, and only one user (me) can use the site. What's more, the data on the server are stored in an Excel table, but not a real database!  
To be honest, the project was only an experiment at that time, testing my skills of table operation and html5 canvas. Very few updates were made during Janurary and Feburary, after adding some functions, I stopped maintaining it for months.  
Until September 2021, after being noticed that I may take part in a contest with this project, I started updating it again. During Mid-Autumn Festival, I worked days and nights and added more than 2k lines of code, adding multi-user system, more memorizing modes and some other functions. Since then, I started maintaining it frequently. Updates are made every weekend (I'm at boarding school so no update can be made during weekday) and new functions are coming out all the time.  
My Memo v5 is a milestone. The appearance changed completely and MySQL database is implemented. The website is becoming a real "website". Group, discovery and many important functions were introduced after that. Better user security, enhanced database performance are also being implemented.  
It's December 2021 when I write this README, and this project is coming to its one year birthday. But I think it's time to complete all the stuff. Main functions and community functions are already added and I don't want to make the site too heavy. Anyhow this is a personal project instead of a business, commercial website.  

**\*Update**: It's 00:00 1st Janurary 2022 when this update is committed. I'd like to say goodbye to 2021 and hello to 2022. I have finished all I want till now. Maybe, that "only bug fixes will be committed in the future" will come true.  

---

## Features  

### 3 Modes

The 3 modes include switch, practice and challenge mode.  
i) **Switch mode**. In switch mode, you will switch between questions and you can click the page to get the answer. Statistics can be shown and you can edit this question. You can also tag / delete the question. Random settings can be applied (Showing questions in the order of question id / randomly)  
ii) **Practice mode**. In practice mode, you will receive questions based on a special random algorithm (it will be introduced later). You can tell whether you memorized the question by clicking Yes and No. Your choice will NOT affect the random algorithm.  
iii) **Challenge mode**. In challenge mode, you will receive questions based on a special random algorithm. Four answers will be displayed and you will be asked to choose the correct one. Your choice will affect the random algorithm.  

**Random algorithm**  
35% rate to display tagged questions  
30% rate to display forgotten questions  
30% rate to display questions that has never been displayed  
5% rate to display status-deleted questions  

**NOTE** There is a status called *Deleted*. It's not really deleting the question but hiding it from daily use. For real deletion, you should find *Remove word*. In most cases, delete refers to status and remove refers to the real removing operation.  

### Book

Books can help you better organize your questions.  
You can create multiple books (there is a limit on my site but you can make it unlimited by updating the config), then bind questions to the book. You should note that, your questions are stored in database which has no connection with books. When adding a question to a book, it's just creating a binding record referring the question to the book. An update on one question will reflect in all books that has included this question.  

For example, suppose you have question A in your database and created Book X, Y, Z.  
A is included in Book X, Y. When you update question A, you can see a content update in book X, Y. When you remove question A, it will disappear in book X, Y.  

### Group

Groups can help you better memorize questions with your friends.  
When creating a group, it's creating a binding record referring the question to the group. When a new user join the group, all the questions-in-group will be added to their own question database and a binding record is created. When editors update / remove a question, it will be synced among all the members.  
Members can tag / delete questions independently as the questions are added to their own database. The progress among members could also be shared, if the owner set the anonymous settings to *Open*.  
Please note that Group creating is disallowed in default on my site. Privilege must be applied by admins before a user can create a group. You can lift this by updating the code on your own site.  

### Discovery

This is a community-based function.  
All users can publish their book / group on Discovery. Others will be able to import the book / join the group. Users can like the post.  
Admins can pin posts on top of the list, usually the post should be announcement post, or a book that has really great contents. Below pinned posts will be normal posts, ordered by the amount of likes and views.  
Admins can also mute users so that they cannot create posts on Discovery. Usually this is done when a user posts inadequate content there.  

### User  

For normal users, the functions are like most other websites. And user security is my main concern during the development. The passwords are salt-hashed with bcrypt to prevent data leak. Sensitive operation will require email verification. And my server is highly protected, firewall applies to all ports except 80 and 443. It is be very very hard to be hacked.  
And there is one highlight that, you can export all your user data at any time. With one click, an Excel table containing your data is generated within seconds and is available for download.  

There are CLI based user management functions for admins.  
Most user permissions are called Privilege including positive & negative permissions, such as allow_group_creation and mute. Details could be seen on CLI page.  

---

## More

**The LICENSE**  
This project is under GNU General Public License. You should open source your site if your code is based on mine. Your contribution is appreciated.  

**The fact of this project**  
The project is a personal project, but not a business / commercial project. It's created completely by personal interest and my love in tech. No profit is earned / planned to be earned.  

**The author**  
The author is a high school student, currently studying at *No.2 High School of East China Normal University, Zizhu Campus* which is a boarding school. The author is busy and can only make updates at weekends.  
The cost of the server is covered by the author himself, using the money earned by remote web development work when I was in junior middle school. I'm only spending them and not earning more as I'm really very busy. Donating will be appreciated and they will only be used to cover the server cost. By the way no ads will be added and they will never appear on my site.  
