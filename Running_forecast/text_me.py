#!/usr/bin/env python3
import sys
import requests
import getopt
# send message to slack
def send_slack_message(message):
    payload = '{"text":"%s"}' % message
<<<<<<< HEAD
    response = requests.post('https://hooks.slack.com/services/your-slack-token',
=======
    response = requests.post('https://hooks.slack.com/services/slack-identification/your-token',
>>>>>>> 0324cf3803213196dbe9d261feae2b0a9f04a809
                            data=payload)
    
    print(response.text) 
def main(argv):
    
    message = ' '
    
    try: opts, args = getopt.getopt(argv, "hm:", ["message="])
        
    except getopt.GetoptError:
        print('text_me.py -m <messsage>')
        sys.exit(2)
    if len(opts) == 0:
        message = "Message par default, tsisy resultat no dikan'izay....!!!!"
    for opt, arg in opts:
        if opt == '-h':
            print('text_me.py -m <message>')
            sys.exit()
        elif opt in ("-m", "--message"):
            message = arg
            
    send_slack_message(message)
    
if __name__ == "__main__":
    main(sys.argv[1:])
