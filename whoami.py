import sys
import logging
logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.INFO,
                    filename="whoami.log")
root = logging.getLogger()
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
root.addHandler(ch)
import websockets
import asyncio
import random
import signal


def signal_handler(signal, frame):
    logging.info("You pressed CTRL-C! Exiting...")
    sys.exit(1)


with open("listofnames.txt",'r') as nameslist:
    LIST_OF_NAMES = list(map(str.strip,nameslist.readlines()))
random.shuffle(LIST_OF_NAMES)

with open("commonwords.txt",'r') as wordslist:
    LIST_OF_WORDS = list(map(str.strip,wordslist.readlines()))
random.shuffle(LIST_OF_WORDS)

USERS = {}
NEXT_NUM = 0

#feel free to change these values
IP = "0.0.0.0"
PORT = 8765

async def register(websocket):
    global NEXT_NUM
    USERS[websocket] = NEXT_NUM
    await websocket.send("yournum:" + str(NEXT_NUM))
    await websocket.send("secret:" + LIST_OF_WORDS[NEXT_NUM])
    NEXT_NUM += 1

async def unregister(websocket):
    del USERS[websocket]

async def server(websocket,path):
    addr=websocket.remote_address[0]
    logging.info("Connection established with {}.".format(addr))
    await register(websocket)
    try:
        async for message in websocket:
            try:
                logging.info('message ' + message)
                number = int(message)
                if number == USERS[websocket]:
                    # Can't request your own number!
                    await websocket.send("You can't request your own number!")
                else:
                    await websocket.send(LIST_OF_NAMES[number])
                    logging.info("sent a name!")
            except IndexError:
                await websocket.send("Invalid number!")
            except ValueError:
                #Maybe the client is requesting a number change
                logging.info('value error')
                try:
                    if message[0:6] == 'secret':
                        newnum = LIST_OF_WORDS.index(message[7:].strip())
                        await websocket.send('yournum:'+str(newnum))
                        await websocket.send(message)
                        USERS[websocket]=newnum
                except IndexError:
                    logging.warning("Received malformed data: {}".format(message))
                except ValueError:
                    logging.warning("Received malformed data: {}".format(message))
    except websockets.exceptions.ConnectionClosed:
        logging.info("Lost connection with {}.".format(addr))
        unregister(websocket)


def main():
    logging.info("Server starting.")
    signal.signal(signal.SIGINT, signal_handler)   
    start_server=websockets.serve(server,IP,PORT)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    main()
