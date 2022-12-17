import time

if __name__ == "__main__": 
    date = ( time.localtime(time.time()) )
    print(type(str(date.tm_mday)))
