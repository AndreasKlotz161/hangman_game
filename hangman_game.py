# © Andreas Schlösser

import random
import time
import os
import sqlite3
import re
import getpass

dbPath = "./hangman_game/hangmangame.db"

# define the hangman stages (currently 8)
hangmanStages = [
    '''
       +-----+
       |     
       |     
       |    
       |     
       |    
    =============
    '''
    ,
    '''
       +-----+
       |     |
       |     
       |    
       |     
       |    
    =============
    '''
    ,
    '''
       +-----+
       |     |
       |     o
       |    
       |     
       |    
    =============
    '''
    ,
    '''
       +-----+
       |     |
       |     o
       |     |
       |     
       |    
    =============
    '''
    ,
    '''
       +-----+
       |     |
       |    \o
       |     |
       |    
       |
    =============
    '''
    ,
    '''
       +-----+
       |     |
       |    \o/
       |     | 
       |    
       |
    =============
    '''
    ,
    '''
       +-----+
       |     |
       |    \o/
       |     |
       |    /
       |
    =============
    '''
    ,
    '''
       +-----+
       |     |
       |     o
       |    /|\\
       |    / \\
       |
    =============
    '''
    ]

#burnman stages (currently 7)
burnmanStages = [
    '''
          
               
           
          
          
          
    ===================
    ''',
        '''
          
               
           
          
           
        xxxxxxx
    ===================
    ''',
    '''
          
               
           
          
         xxxxx
        xxxxxxx
    ====================
    ''',
    '''
          
           0
          /|\\ 
          / \\
         xxxxx
        xxxxxxx
    ====================
    ''',
    '''
          
           0     \33[31m§\33[0m
          /|\\    |
          / \\    \\0
         xxxxx     |
        xxxxxxx    /\\
    ====================
    ''',
    '''
          
           0      
          /|\\    
          / \\      0
         xxxxx  \33[31m§\33[0m_/|
        xxxxxxx    /\\
    ====================
    ''',
    '''
          
           0      
          /|\\    
          / \\  
         \33[31m§\33[0m\33[33m§\33[0m\33[31m§\33[0m\33[33m§\33[0m\33[31m§\33[0m
        xxxxxxx
    ====================
    '''
]

# burnman endanimation pictures
burningmanEnd = [
    '''
          
           0      
          /|\\    
          \33[33m§\33[0m\33[31m§\33[0m\33[31m§\33[0m  
         \33[31m§\33[0m\33[33m§\33[0m\33[31m§\33[0m\33[33m§\33[0m\33[31m§\33[0m
        xxxxxxx
    ====================
    ''',
    '''
          
           0      
          /|\\    
          \33[31m§\33[0m\33[33m§\33[0m\33[33m§\33[0m  
         \33[33m§\33[0m\33[31m§\33[0m\33[33m§\33[0m\33[31m§\33[0m\33[33m§\33[0m
        xxxxxxx
    ====================
    '''
    
]

#list of insults to be thrown at user if it misbehaves from perplexity prompt
pirateInsults = [
    "Ye scurvy dog!",
    "Ye bilge-sucking scallywag!",
    "Ye barnacle-brained swab!",
    "Ye mangy sea rat!",
    "Ye lily-livered landlubber!",
    "Ye rum-soaked deck swabber!",
    "Ye barnacle-covered bilge rat!",
    "Ye addle-brained cabin boy!",
    "Ye slack-jawed son of a sea cook!",
    "Ye grog-addled sea slug!",
    "Ye worm-ridden scupper plug!",
    "Ye salt-crusted scallywag!",
    "Ye fish-brained lubber!",
    "Ye gull-bothering deck ape!",
    "Ye kraken-baiting fool!"
]

#initialises the database for the game if it does not exist
#add the Admin and a high level user(Peter, for testing puposes) to Users
def initDatabase():
    if not os.path.isfile(dbPath):
        con = sqlite3.connect(dbPath)
        cur = con.cursor()
        #default list of words, mostly generated with perplexity
        words = [
            ("HELLO WORLD", "Common beginner task", 0),
            ("EGG", "What was first?", 0),
            ("HEN", "What was second?", 0),
            ("BOOLEAN", "A datatype and human", 0),
            ("SCHROEDINGER", "A well known kitty torturer", 1),
            ("RANTANPLAN", "A very smart dog", 1),
            ("GUITARRERO", "A spanish guitarist", 1),
            ("COMPUTER", "Mashed up minerals for calculating stuff", 1),
            ("WHISTLE", "Something that makes a sound when you blow it.", 2),
            ("JOURNEY", "A trip from one place to another.", 2),
            ("CAPTURE", "To take something or someone by force.", 2),
            ("TWILIGHT" , "Light just before nightfall.", 2),
            ("EPHEMERAL", "Lasting for a very short time.", 3),
            ("OBSIDIAN", "A dark volcanic glass. Can only be gathered with netherite or diamond pickaxe", 3),
            ("LABYRINTHINE", "Complicated, like a maze.",3),
            ("SERENDIPITY", "Finding something good by accident", 3)]
        
        #create tables for words users and passwords
        cur.execute('CREATE TABLE words(id INTEGER PRIMARY KEY AUTOINCREMENT, word TEXT, hint TEXT, difficulty INTEGER)')
        cur.execute('''CREATE TABLE users(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, difficulty INTEGER DEFAULT 0 NOT NULL, 
                                          points INTEGER DEFAULT 0 NOT NULL, empowered BOOLEAN DEFAULT False NOT NULL)''')
        cur.execute('CREATE TABLE passwords(user_id INTEGER,password TEXT, FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)')
        con.commit()

        #insert all words from the default list
        cur.executemany('INSERT INTO words(word,hint,difficulty) VALUES (?, ?, ?)', words)
        con.commit()
        
        #insert Admin to database
        cur.execute('INSERT INTO users(name) VALUES ("Admin")')
        userID = cur.execute('SELECT id FROM users WHERE name="Admin"').fetchall()[0][0]
        cur.execute('INSERT INTO passwords(user_id, password) VALUES (?, ?)', [userID, "safePW"])
        
        #insert high ranked user to database
        cur.execute('INSERT INTO users(name, difficulty, points, empowered) VALUES ("Peter", 3, 2400, True)')
        userID = cur.execute('SELECT id FROM users WHERE name="Peter"').fetchall()[0][0]
        cur.execute('INSERT INTO passwords(user_id, password) VALUES (?, ?)', [userID, "123"])

        con.commit()
        #close connection
        con.close()

# single game of hangman: returns True if won and False if not
#@param goal a tuple is expected (WORD,HINT,DIFFICULTY) 
def hangmanGame(goal=set):
    #list of guessed chars not in the word
    charsMissed = []
    #list of worng guessed words
    wrongWords = []
    #counter for failures(counts only first wrong guesses of single letters or words matching the number of letters in the goal word)
    fails = 0
    #set the current word to all dashes or space
    currentWord = "".join([" " if x == " " else "-" for x in goal[0]])
    #placeholder for the hint
    hint = ""
    #delete all text in terminal
    os.system("cls")
    print()
    #### main game loop ####
    while True:
        #print the stage depending on number of failures
        print(hangmanStages[fails])
        print(f"Wrong guessed words: {' | '.join(wrongWords)}")
        print(f"Letters not in word: {' | '.join(charsMissed)}")
        print(f"Word: {currentWord}")
        #check if won and return true if so
        if currentWord == goal[0]:
            print("You guessed it right!")
            time.sleep(3)
            return True
        #check if last stage of hangman was reached -> loose and return false
        elif fails == len(hangmanStages)-1:
            print(f"You have had your trys and loose! The word was \33[33m{goal[0]}\33[0m.p" + getRandomInsult())
            time.sleep(3)
            return False
        #else get a user input for next try
        else:
            guess = input(f"{hint}\nEnter your guess ----> ").upper()
            #check if the user entered rubbish (word not matching the length of the goal or no letter from ABC)
            if (len(guess) > 1 and len(guess) != len(goal[0])) or (len(guess) == 1 and "ABCDEFGHIJKLMNOPQRSTUVWXYZ".find(guess) == -1):
                #if so print error message and retry
                os.system("cls")
                print("Only enter single letters of the english alphabet ('ABCDEFGHIJKLMNOPQRSTUVWXYZ') or the whole word." + getRandomInsult())
                continue
            #check if the user has allready guess that worng one time
            elif guess in charsMissed or guess in wrongWords:
                #if thats the case display this errormessage and retry
                os.system("cls")
                print(f"You hav allready tried \33[34m{guess}\33[0m" + getRandomInsult())
                continue
            #do this if there is a valid new guess
            else:
                #renew current word by calling the checkGuess function
                #giving it the current guess, currently guessed word and the goal word
                #c is empty string guess was correct
                #c is guess if guess was not in the goalword or the goalword
                #c is used here also like a boolean
                currentWord, c = checkGuess(guess, currentWord, goal[0])
                #if there is something in c and goalword was not entered
                if c and goal[0] != currentWord:
                    #if c contains a single letter
                    if len(c) == 1:
                        charsMissed.append(c)
                    #if c contains a word
                    else:
                        wrongWords.append(c)
                    #both cases above count aas a failed attempt
                    fails += 1
                    #if there where two plus difficulty(0-3) failed attempts
                    if fails == 2 + goal[2]:
                        os.system("cls")
                        print(getRandomInsult().strip() + "\nIt seems to hard for you...")
                        #ask the user if it wants to get a hint
                        if input("Do you want to get a hint? (Y.es / N.o):\n").strip().upper() in ("Y", "YES"):
                            #set the hint to display
                            hint = "\33[32m~~~~ Hint: " + goal[1] + " ~~~~\33[0m"
                            #show the hint for a short time
                            print("\n" + hint)
                            time.sleep(2.5)
                #clear terminal for new print loop
                os.system("cls")
                print()
                continue

# single game of burnman: returns True if won and False if not
#@param goal a tuple is expected (WORD,HINT,DIFFICULTY) 
def burnmanGame(goal=set):
    #list of guessed chars not in the word
    charsMissed = []
    #list of worng guessed words
    wrongWords = []
    #counter for failures(counts only first wrong guesses of single letters or words matching the number of letters in the goal word)
    fails = 0
    #set the current word to all dashes or space
    currentWord = "".join([" " if x == " " else "-" for x in goal[0]])
    #placeholder for the hint
    hint = ""
    #delete all text in terminal
    os.system("cls")
    print()
    #### main game loop ####
    while True:
        #print the stage depending on number of failures
        print(burnmanStages[fails])
        print(f"Wrong guessed words: {' | '.join(wrongWords)}")
        print(f"Letters not in word: {' | '.join(charsMissed)}")
        print(f"Word: {currentWord}")
        #check if won and return true if so
        if currentWord == goal[0]:
            print("You guessed it right!")
            time.sleep(3)
            return True
        #check if last stage of hangman was reached -> loose and return false
        elif fails == len(burnmanStages)-1:
            time.sleep(1.5)
            for i in range(11):
                os.system("cls")
                print(f"You have had your trys and loose! The word was \33[33m{goal[0]}\33[0m.p" + getRandomInsult())
                print(burningmanEnd[i%2])
                time.sleep(0.5)
            return False
        #else get a user input for next try
        else:
            guess = input(f"{hint}\nEnter your guess ----> ").upper()
            #check if the user entered rubbish (word not matching the length of the goal or no letter from ABC)
            if (len(guess) > 1 and len(guess) != len(goal[0])) or (len(guess) == 1 and "ABCDEFGHIJKLMNOPQRSTUVWXYZ".find(guess) == -1):
                #if so print error message and retry
                os.system("cls")
                print("Only enter single letters of the english alphabet ('ABCDEFGHIJKLMNOPQRSTUVWXYZ') or the whole word." + getRandomInsult())
                continue
            #check if the user has allready guess that worng one time
            elif guess in charsMissed or guess in wrongWords:
                #if thats the case display this errormessage and retry
                os.system("cls")
                print(f"You hav allready tried \33[34m{guess}\33[0m" + getRandomInsult())
                continue
            #do this if there is a valid new guess
            else:
                #renew current word by calling the checkGuess function
                #giving it the current guess, currently guessed word and the goal word
                #c is empty string guess was correct
                #c is guess if guess was not in the goalword or the goalword
                #c is used here also like a boolean
                currentWord, c = checkGuess(guess, currentWord, goal[0])
                #if there is something in c and goalword was not entered
                if c and goal[0] != currentWord:
                    #if c contains a single letter
                    if len(c) == 1:
                        charsMissed.append(c)
                    #if c contains a word
                    else:
                        wrongWords.append(c)
                    #both cases above count aas a failed attempt
                    fails += 1
                    #if there where two plus difficulty(0-3) failed attempts
                    if fails == 2 + goal[2]:
                        os.system("cls")
                        print(getRandomInsult().strip() + "\nIt seems to hard for you...")
                        #ask the user if it wants to get a hint
                        if input("Do you want to get a hint? (Y.es / N.o):\n").strip().upper() in ("Y", "YES"):
                            #set the hint to display
                            hint = "\33[32m~~~~ Hint: " + goal[1] + " ~~~~\33[0m"
                            #show the hint for a short time
                            print("\n" + hint)
                            time.sleep(2.5)
                #clear terminal for new print loop
                os.system("cls")
                print()
                continue

#checks if a given guess is in the goalword and return a new value and an empty string for currentWord based on that
#also checks if the goal word was entered and then return the goal word and an empty string
#if the guess is not in the goal word or is not the goal word, it returns the currentWord unchanged and the Wrong guess
#@param guess: guess to validate
#@param currWord: currently status of the word, will be returned if the check fails
#@param goal: the goal word, wich the guess will be tested against
def checkGuess(guess=str, currWord=str, goal=str):
    #guess is goal
    if guess == goal:
        return (goal, "")
    #guess is in goal
    elif len(guess) == 1 and guess in goal:
        # get a list of guessed letters from current word and add guessed letter and a space
        validLetters = re.findall(r"[A-Z]{1}", currWord) + [guess, " "]
        #return new current word replacing all not guessed letters with a dash
        return ("".join([x if (x in validLetters) else "-" for x in goal]), "")
    #wrong guess
    else:
        #return currWord unchanged, and the wrong guess
        return(currWord, guess)

#creates a new user in database if the name does not exist and returns taht new user else it returns an empty tuple
def newUser():
    #connect to database
    con = sqlite3.connect(dbPath)
    cur = con.cursor()
    os.system("cls")
    print("\n*** NEW USER ***")
    #get new username
    userName = input("Enter your name: \n")
    #check if this username exists in database
    if cur.execute('SELECT name from users WHERE name = ?', [userName]).fetchall():
        print(f"This username ({userName}) allready exists." + getRandomInsult())
        #if so return an empty tuple == return False
        return()
    else:
        #aks the user for a password
        userPass = getpass.getpass("Enter your password: ")
        #confirm the password
        if userPass == getpass.getpass("Confirm your password: "):
            #then add user to user table
            cur.execute('INSERT INTO users(name) VALUES(?)', [userName])
            #get its ID
            userID = cur.execute('SELECT id FROM users WHERE name = ?', [userName]).fetchall()[0][0]
            #and add password to the passwordtable
            cur.execute('INSERT INTO passwords(user_id, password) VALUES (?, ?)', [userID, userPass])
            con.commit()
            #get Values of this new user to log in 
            user = cur.execute('SELECT name, difficulty, points, empowered FROM users WHERE id = ?', [userID]).fetchall()[0]
            con.close()
            return user
        #password was not confirmed return empty tuple == retrun  FAlse
        return ()

#this saves difficulty, points and empowered status to the users table by users name
#@param name: the users name to select the record in table users
#@param diffi: the difficulty level of user
#@param points: the points of user
#@param empowered: the status of the users entitlement for adding new words
def saveUserData(name=str, diffi=int, points=int, empowered=bool):
    con = sqlite3.connect(dbPath)
    cur = con.cursor()
    cur.execute('UPDATE users SET difficulty= ?, points= ?, empowered= ? WHERE name= ?', [diffi, points, empowered, name])
    con.commit()
    con.close()

#displays all words in the database and lets user delete one per page or all Words
def showWords():
    con = sqlite3.connect(dbPath)
    cur = con.cursor()
    #get all words and their ids from database
    wordList = [x for x in cur.execute('SELECT id, word FROM words ORDER BY id')]
    #if there are no words in the database
    if not wordList:
        print("There are no words in the database." + getRandomInsult())
        time.sleep(2)
        return
    #loop through the list 10 items a time x is the start index of the partial list
    for x in range(0, len(wordList), 10):
        os.system("cls")
        # calculate the end of the partial list
        end = x+10 if x+10 < len(wordList) else len(wordList)
        #print title and current item range
        print(f"*** SHOW WORDS ***\nWords " + (f"{end}" if x+1 == end else f"{x+1}-{end}") + " of {len(wordList)}")
        #print each elemt of the partial list
        for elem in wordList[x:end]:
            print(f"\tID: {elem[0]:>4}\t{elem[1]}")
        #ask the user if to delete anything or the whole list
        opt = input("Enter ID of word to delete it or A.ll to delete all words." +
                    #display message depending on wether its the last partial list
                    ("\nPress enter to see the next ten words" if end != len(wordList) else "\nPress enter to escape") +
                    "\n---> ").strip().upper()
        if opt in ("A", "ALL"):
            #delete all words
            cur.execute("DELETE FROM words")
            break
        elif opt.isnumeric():
            #try to delete item on enterd index
            try:
                opt = int(opt)
                #check if given index is in partial list
                if opt in [elem[0] for elem in wordList[x:end]]:
                    # if it is delete its record
                    cur.execute('DELETE FROM words WHERE id= ?', [opt])
                    print(f"Word with ID {opt} was deleted.")
                    time.sleep(1.5)
                else:
                    print("Invalid ID." + getRandomInsult())
                    time.sleep(1.5)
            except Exception as e:
                print("Invalid ID." + getRandomInsult())
                time.sleep(1.5)
    con.commit()
    con.close()

#show all users except Admin optional deleting specific user or all (except Admin)
def showUsers():
    con = sqlite3.connect(dbPath)
    cur = con.cursor()
    #activate foreign key references to cascade on delete
    cur.execute("PRAGMA foreign_keys = ON")
    #get all users from database
    userList = [x for x in cur.execute('SELECT id, name FROM users WHERE name != "Admin" ORDER BY id')]
    #if there are no users in the database
    if not userList:
        print("There are no users in the database." + getRandomInsult())
        time.sleep(2)
        return
    #go through users in groups of ten x is the start index of the sublist
    for x in range(0, len(userList), 10):
        os.system("cls")
        #calculate the end of the sublist
        end = x+10 if x+10 < len(userList) else len(userList)
        #print the title and the range of the sublist
        print(f"*** SHOW USERS ***\nUser " + (f"{end}" if x+1 == end else f"{x+1}-{end}") + "of {len(userList)}")
        #go through each user of the sublist
        for elem in userList[x:end]:
            #print that user and its ID
            print(f"\tID: {elem[0]:>4}\t{elem[1]}")
        #ask if to delete all or specific or if to just show the next partial list
        opt = input("Enter ID of user to delete it or A.ll to delete all users." +
                    #depending on if its the last sublist print different message
                    ("\nPress enter to see the next ten users" if end != len(userList) else "\nPress enter to escape") +
                    "\n---> ").strip().upper()
        if opt in ("A", "ALL"):
            #delete all user except Admin
            cur.execute('DELETE FROM users WHERE name != "Admin" ')
            break
        elif opt.isnumeric():
            #try to delete usser with specific id
            try:
                opt = int(opt)
                #if user is in sublist
                if opt in [elem[0] for elem in userList[x:end]]:
                    #delete taht user
                    cur.execute('DELETE FROM users WHERE id= ?', [opt])
                    print(f"User with ID {opt} was deleted.")
                    time.sleep(1.5)
                else:
                    print("Invalid ID." + getRandomInsult())
                    time.sleep(1.5)
            except:
                print("Invalid ID." + getRandomInsult())
                time.sleep(1.5)
    con.commit()
    con.close()

#calculates the difficulty of a word. this is not that serious just playing around.
#not tested for usage but is used
#returns either 0=very easy, 1=easy, 2=hard, very hard
#@param word: the word to be staged     
def getDiffi(word=str):
    #three categories of letters by occurance in english words
    #got lists from perplexity prompt 
    often = ("E", "T", "A", "O", "N", "I", "S", "R", "H", "L", "D")
    common = ("U", "C", "M", "W", "Y", "F", "G", "P", "B", "V", "K")
    rare = ("J", "X", "Q", "Z")

    #set difficulty for a word by its length
    #the lower this value the easier the word
    diffi = len(word)
    for x in word:
        if x in often:
            diffi -= 0.9
        elif x in common:
            diffi -= 0.6
        elif x in rare:
            diffi -= 0.2
    #return value depending on calculated difficulty
    if diffi < 0.6:
        return 0
    elif diffi < 1.3:
        return 1
    elif diffi < 2.4:
        return 2
    else:
        return 3        

#lets the user enter a new word and a hint for the hangman database if its not allready in the database
#calculates the difficulty by using getDiffi()
def enterNewWord():
    con = sqlite3.connect(dbPath)
    cur = con.cursor()
    #show title of the subprogram
    os.system("cls")
    print("*** ENTER A NEW WORD ***\n\n")
    #asks the user to enter a new word/words and delete whitspace around it
    word = input("Enter a new word:\n").upper().strip()
    #check if the word is not in the database and consists of at least one letter
    if not cur.execute('SELECT word FROM words WHERE word= ?', [word]).fetchall() and re.match(r"[A-Z ]?", word):
        #then let user enter a hint
        hint = input(f"Enter your hint for {word}:\n")
        #caculate the difficulty
        diffi = getDiffi(word)
        #show what will be put to database
        print(f"{word} (Hint: {hint}, calculated Difficulty {diffi+1})")
        #user can enter a new difficulty or keep it or escape the whole process
        newDiffi = input("Press enter if you want to keep difficulty or enter a new difficulty between 1-4\n" +
                         "Enter E.scape to disrupt\n---> ").upper()
        if newDiffi:
            #if escape
            if newDiffi in ("E", "ESCAPE"):
                #close connection and return to menu
                con.close()
                return None

            try:
                if newDiffi in (1,2,3,4):
                    diffi = int(newDiffi)-1
                else:
                    print("\nYou are to stupid to enter a number between 1 and 4, so the calculated difficulty will be used." + getRandomInsult())
                    time.sleep(3)
            except:
                print("\nYou are to stupid to enter a number between 1 and 4, so the calculated difficulty will be used." + getRandomInsult())
                time.sleep(3)
        #put new word into database
        cur.execute('INSERT INTO words(word, hint, difficulty) VALUES(?,?,?)', [word,hint,diffi])
        con.commit()
    #if word is allready in database or is no valid word
    else:
        print(f"Either \33[34m{word}\33[0m allready exists in the database or\n" +
              "it does not consist of at least one letter of those from the english alphabet.\n" + getRandomInsult())
        time.sleep(3)
    con.close()

#returns a random pirate slur from the list
def getRandomInsult():
    #return a random word (and its hint)
    return " " + pirateInsults[random.randint(0, len(pirateInsults)-1)]

#returns a random word (WORD, HINT, DIFFICULTY) from the word table depending on difficulty
#@param diffi: difficulty of random word
def getRandomWord(diffi=int):
    con = sqlite3.connect(dbPath)
    cur = con.cursor()
    #get all words of that diffi level
    wordsOfDiffi = cur.execute('SELECT word, hint, difficulty FROM words WHERE difficulty = ?', [diffi]).fetchall()
    con.close()
    #return a random word (and its hint)
    return wordsOfDiffi[random.randint(0, len(wordsOfDiffi)-1)]

#shows the current rankingtable of all users
def showRanking():
    con = sqlite3.connect(dbPath)
    cur = con.cursor()
    #the rankinglist orderd by user points
    rankedList = enumerate(cur.execute('SELECT name, points FROM users WHERE name != "Admin" ORDER BY points DESC').fetchall(), start=1)
    con.close()
    os.system("cls")
    # put it in a string var for maybe printing it to a document later
    rankedListForPrint = ""
    #print tableheader
    rankedListForPrint += "Rank |   Name                |  Points\n"
    rankedListForPrint += "--------------------------------------\n"
    #add new line for each record
    for e in rankedList:
        #formated strings with whitespaces to allign to the tableheader
        rankedListForPrint += f"{e[0]:>3}  |   {e[1][0]:<20}|{e[1][1]:>8}\n"
    #print the result and pause the program til enter is pressed
    print(rankedListForPrint)
    input("Press enter to return.")

#shows the login menu and lets the user choose to login create new account or exit the program
#returns a User tuple: (NAME, DIFFICULTY, POINTS, EMPOWERED(=can user create new words))
#                     if logging in was successful or successfully created new user
#returns empty tuple if the user enters exit in the login loop
def login():
    #set user as empty tuple its the condition for relooping if the user enterd wrong data
    user = ()
    #############login loop#############
    while not user:
        os.system("cls")
        #diplay the menu
        print("+++ HANGMAN - LOGIN +++")
        #get users choice
        opt = input("\nL.ogin | N.ew user | E.xit\n----> ").upper()
        #login as existing user
        if opt in ("L", "LOGIN"):
            con = sqlite3.connect(dbPath)
            cur = con.cursor()
            #get userID by searching for name in database
            userID = cur.execute('SELECT id FROM users WHERE name = ?',[input("Enter your username:\n")]).fetchall()
            #if userid was found(user exists)
            if userID:
                #save that ID
                userID = userID[0][0]
                #select user password by id
                userPass = cur.execute('SELECT password FROM passwords WHERE user_id = ?', [userID]).fetchall()[0][0]
                #check if the user entered the correct password
                if userPass == getpass.getpass("Enter your password: "):
                    #set user by that users ID ()
                    user = cur.execute('SELECT name, difficulty, points, empowered FROM users WHERE id = ?', [userID]).fetchall()[0]
                    con.close()
                    print("\n\nLogged in successfully.")
                    time.sleep(1)
                else:
                    print("\n\nWrong password." + getRandomInsult())
                    time.sleep(1)
                    continue
            else:
                print("\n\nUser does not exist." + getRandomInsult())
                time.sleep(2)
                continue
        elif opt in ("N", "NEW", "NEW USER"):
            #try to create new user(either a valid user tuple is returned from newUser or an empty tuple)
            user = newUser()
        elif opt in ("E", "EXIT"):
            break
        else:
            os.system("cls")
            print(f"\n\33[33m{opt} is not a valid option.\33[0m." + getRandomInsult())
            time.sleep(1)
    return user

#the main menu and entrypoint for the program
#displays a menu for administration or normal users depending on user name
#first calls the login menu to get a user name
def hangmanMenu():
    #set user by calling the login menu gets empty set or (NAME, DIFFICULTY, POINTS, EMPOWERED)
    user = login()
    #if a user is set, unpack its values
    if user:
        userName, userDifficulty, userPoints, allowNewWords = user
    ########### main menu loop##############
    ###### entered if a user is set #########
    while user:
        #clear terminal
        os.system("cls")
        ######## menu for admin ############
        if userName == "Admin":
            #display menu header
            print(f"+++ HANGMAN - MENU +++  \33[33m<> LOGGED IN AS: {userName} <>\33[0m")
            #display options and get users choice
            opt = input("\nP.lay game | N.ew W.ord | D.isplay W.ords | N.ew U.ser | D.isplay U.sers | L.og out | E.xit\n\n----> ").upper()   
            #test game by entering a level
            if opt in ("P", "PLAY", "PLAY GAME"):
                try:
                    hangmanGame(getRandomWord(int(input("Enter a difficulty level (0-3) you want to try: "))))
                except:
                    print("You have to enter a valid difficulty level." + getRandomInsult())
            #enter a new word
            elif opt in ("NW", "NEW WORD"):
                enterNewWord()
            #show all words optional delete
            elif opt in ("DW", "DISPLAY WORDS"):
                showWords()
            #enter new user
            elif opt in ("NU", "NEW USER"):
                newUser()
            #show all users optional delete
            elif opt in ("DU", "DISPLAY USERS"):
                showUsers()
            #new login to change user
            elif opt in ("L", "LOG", "LOG OUT"):
                user = login()
                #change user data
                if user:
                    userName, userDifficulty, userPoints, allowNewWords = user
            #exit program
            elif opt in ("E", "EXIT"):
                user = ()
            else:
                print(f"\33[33m{opt} is not a valid option.\33[0m." + getRandomInsult())
        ###### menu for all other users #########
        else:
            #diplay menu header for user with name, points and users current difficulty
            print("+++ HANGMAN - MENU +++  \33[33m<> LOGGED IN AS: "+ userName + " <>\33[0m Points: "+ str(userPoints) + " Difficulty: " +
                  #select the string to display current difficulty
                  ["\033[32mEASY\033[0m","\033[33mPEASY\033[0m","\033[31mLEMON\033[0m","\033[35mSQUEEZY\033[0m"][userDifficulty])
            #display options and ask the user what to do.
            opt = input("\nP.lay game | S.et Difficulty "+
                        #if access is granted, show option to enter new words
                        ("| N.ew Word " if allowNewWords else "")+
                        "| R.anking\n\nL.og out | E.xit\n\n----> ").upper()
            #play game if win add points by difficulty, if loose subtract 100 points
            if opt in ("P", "PLAY", "PLAY GAME"):
                choose = input("B.urn or H.ang ").strip().upper()
                if choose in ("B", "BURN"):
                    if burnmanGame(getRandomWord(userDifficulty)):
                        userPoints += 100* (userDifficulty+1)
                    else:
                        userPoints -= 100
                    #update user stats by points
                    if userPoints < 500:
                        userDifficulty = 0
                        allowNewWords = False
                    elif userPoints < 1000:
                        userDifficulty = 1
                        allowNewWords = False
                    elif userPoints < 2000:
                        userDifficulty = 2
                        allowNewWords = True
                    else:
                        userDifficulty = 3
                        allowNewWords = True
                elif choose in ("H", "HANG"):
                    if hangmanGame(getRandomWord(userDifficulty)):
                        userPoints += 100* (userDifficulty+1)
                    else:
                        userPoints -= 100
                    #update user stats by points
                    if userPoints < 500:
                        userDifficulty = 0
                        allowNewWords = False
                    elif userPoints < 1000:
                        userDifficulty = 1
                        allowNewWords = False
                    elif userPoints < 2000:
                        userDifficulty = 2
                        allowNewWords = True
                    else:
                        userDifficulty = 3
                        allowNewWords = True
                else:
                    print("Your choice does not exist.")
                    time.sleep(2)
            #set the difficulty for next game by user input with low error handling
            elif opt in ("S", "SET", "SET DIFFICULTY"):
                newDiffi = input("Enter the difficulty for the next game (1-4): ")
                try:
                    newDiffi = int(newDiffi)-1
                    if -1 < newDiffi < 4:
                        userDifficulty = newDiffi
                    else:
                        print("Invalid value for difficulty." + getRandomInsult())
                        time.sleep(1)
                except:
                    print("You have to enter a number." + getRandomInsult())
                    time.sleep(1.5)
            #option to enter a new word if user is allowed
            elif opt in ("N", "NEW", "NEW WORD") and allowNewWords:
                enterNewWord()
            #display current ranking
            elif opt in ("R", "RANKING"):
                #therefore update database with current users data
                saveUserData(userName, userDifficulty, userPoints, allowNewWords)
                #then display
                showRanking()
            #log out.... and open login menu
            elif opt in ("L", "LOG", "LOG OUT"):
                #fisrt save the user data
                saveUserData(userName, userDifficulty, userPoints, allowNewWords)
                #then get new user
                user = login()
                if user:
                    userName, userDifficulty, userPoints, allowNewWords = user
            #save user data and exit
            elif opt in ("E", "EXIT"):
                saveUserData(userName, userDifficulty, userPoints, allowNewWords)
                user = ()
            else:
                print(f"\33[33m{opt} is not a valid option.\33[0m" + getRandomInsult())
                time.sleep(2)

###########################################
##################RUN######################
###########################################

# initializes database if it does not exist
initDatabase()
#starts program loop
hangmanMenu()