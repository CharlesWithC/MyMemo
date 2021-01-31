# WordMemorizer
*A light word / phrase memorizer made with python flask + html5 canvas*

*It's only tested in python3.8 + Chrome browser environment. But it should support python3.\* and most browsers.*

## How to install
### First, prepare the dataset.
Simply create a Excel Table, save it as `data.xlsx` and put it in the folder where the script will be ran.
### Next, install dependencies
`python3 -m pip install flask`
### Then, run the code
`python3 app.py`
### Finally, open your browser and enter URL `localhost:5000`
**You can change the port manually, just edit the last line of app.py** \
For example, if you want the app to run on 80 port, kindly change that line of code to `app.run("0.0.0.0",80)`

## How to use
There are settings buttons on the webpage, click them to alter the settings. The text it's showing means the current settings.\
Once you finished the settings, you could choose to enter a word / phrase in the inputbox (it's optional). Then press `Start`.\
You can `Tag` / `Untag` the words / phrases, they will be hidden if you chose `Do not show tagged words` in the settings.\
The script will store your progress in Local Storage and allow you to restart from it when you reopen the page.

## More Info
Please open an issue if you met any bugs during the use.
You could also open an issue for good suggestions and I'll decide whether to add it.
And finally, it's "Coffee Time". You could donate some Bitcoin to `1NKaAbrGyBa52YqvTbs6vasQYVvhWvP16k` / `bc1qzktkmjnmxsjerezsakt964mygvp8mkxr45xtsc`  or Litecoin to `ltc1qgfkkmy8mkxtqrm3s3enu6cx63r40hcvng3qqdj`
