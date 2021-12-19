# Email Remote  

This script should run on a separate server from main server.  
That server should have postfix installed and configured and is used to send mails.  
Using a separate server can help protect main server's ip.  

Don't worry that your mail server will be abused by spam, as a key is needed to send the email. The key is encrypted during the connection.  
By the way, you can also add a firewall to allow only main server to make requests.  