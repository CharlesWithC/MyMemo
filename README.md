# WordMemorizer
*A light word / phrase memorizer made with python flask + html5 canvas*

*It's only tested in python3.8 + Chrome / Firefox browser environment. But it should support python3.\* and most browsers.*

## How to install
### 0.Clone this repo
`git clone https://github.com/Charles-1414/WordMemorizer`
### 1.Prepare the dataset.
Simply create a Excel Table, save it as `data.xlsx` and put it in the folder where the script will be ran.\
**The headings must be 'Word','Pronounciation','Definition'**\
You can update this table using your browser in the future.
### 2.Install dependencies
`python3 -m pip install flask`
### 3.Run the code
`python3 app.py`
### 4.Open your browser and enter URL `localhost:8888`
**You can change the port manually, just edit the last line of app.py** \
For example, if you want the app to run on 80 port, kindly change that line of code to `app.run("0.0.0.0",80)`

## Usage
### It's easy to use, just click around and you'll find how to use
To upload new data at client side, press the "Upload" button in the right-bottom cornor of the home page. Then enter the Upload Password and upload the file. The default password is 123456. You can change it at /changepwd

## More Info
Please open an issue if you met any bugs during the use.
You could also open an issue for good suggestions and I'll decide whether to add it.
And finally, it's "Coffee Time". You could donate some Bitcoin to `1NKaAbrGyBa52YqvTbs6vasQYVvhWvP16k` / `bc1qzktkmjnmxsjerezsakt964mygvp8mkxr45xtsc`  or Litecoin to `ltc1qgfkkmy8mkxtqrm3s3enu6cx63r40hcvng3qqdj`
