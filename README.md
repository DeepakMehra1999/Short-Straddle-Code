# Short-Straddle-Code
Short Straddle is an options trading strategy where trader sells both a call option and a put option with the same strike price and expiration date. 
Here I am using Zerodha Kite Connect to execute strategy. The idea behind the strategy to execute straddle at 9:30 and place stoploss above 25% of selling prices. If any of the stoploss hits(assume it hits of call option) than it modifies the stoploss of put option at cost(means at the selling price). For squareoff the position, it checks if premium decays by 80% or if time is 15:15 noon, it squareoff the open positions.

Note :- 
1) Overall there are 2 Python Script and 1 text file named as Input_File.txt
2) Before starting, Make sure your Input_file.txt and Python scripts are in same directory.
3) Check once in Input_File.txt, that key and secret have their respective values. 


Instructions:

1) First step, is to run Login_Kite.py script. After running the script, you will get login URL, just copy and paste it in your chrome, preferably in Incognito mode.
2) After hitting enter, there you will get value of request token, copy it and paste it in req_token variable in an Input_File.txt and save it.
3) After this, just comment the line no. 23(print(kite.login_url())) and uncomment the line of gen_ssn,acc_tkn,print(acc_tkn) from the script.
4) Again, run the code, see the output, you will get access_token for the day. Copy it, paste it to access_token variable in an Input_File.txt and save it.
5) Now, Comment the lines which you commented in step no. 4, and uncomment the line which you commented in step no. 3 for next day.
6) Now, the work of generate_token.py is completed and you get request_token and access_token, and you have their values in an Input_File.txt.
7) Now, run the file of Long_Straddle_Code.py, to start Algo Trading.

