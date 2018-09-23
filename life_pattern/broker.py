import paho.mqtt.client as mqttClient
import time
import csv
import numpy as np
import random
import threading

global csvfile
global csvfile2

global gravity
global seconds
global standardData
global lastSwitchTime
global Switch, Pending, init
global sequence
global counter
global secondCounter
global numInSecond
global data
global threadRunning
global stopThread




def target():
    global client
    global threadRunning
    threadRunning=True
    print('the curent threading  %s is running' % threading.current_thread().name)
    while stopThread!=True:
        time.sleep(1)
        localtime = time.asctime(time.localtime(time.time()))
        client.publish("python/test","T {}".format(str(localtime)))
    client.publish("python/test", "D ")
    print('the curent threading  %s is ended' % threading.current_thread().name)
    threadRunning=False




def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to broker")
        global Connected  # Use global variable
        Connected = True  # Signal connection
    else:
        print("Connection failed")


def checkSatisfied(gravity):
    # Check whether the gesture is within the standard.
    global standardData
    tol = 0.5
    limit = 0.3
    satisfied = True
    if abs(gravity[0] - standardData[0]) > limit:
        satisfied = False
        tol = tol - abs(gravity[0] - standardData[0])
    if abs(gravity[1] - standardData[1]) > limit:
        satisfied = False
        tol = tol - abs(gravity[1] - standardData[1])
    if abs(gravity[2] - standardData[2]) > limit:
        satisfied = False
        tol = tol - abs(gravity[2] - standardData[2])
    if tol < 0:
        satisfied = False
    if (satisfied):
        return True
    else:
        return False

def processApplication(context):
    global sequence
    global counter
    #print (context)
    if (counter <= 99):
        sequence[counter, 0] = float(context[2])
        sequence[counter, 1] = float(context[3])
        sequence[counter, 2] = float(context[4])
        counter += 1
        # print(counter)
    else:
        newSequence = np.zeros((100, 3))
        # print (sequence)
        newSequence[0:-1, :] = sequence[1:, :]
        newSequence[-1, 0] = float(context[2])
        newSequence[-1, 1] = float(context[3])
        newSequence[-1, 2] = float(context[4])
        # output newSequence here
        sequence = newSequence

        #which_pattern(np.array([sequence]))


def padding(data):
    #data list
    global numInSecond
    newData=[]
    x=len(data)
    print(x)
    if x > 6:
        if x < numInSecond:
            newIndex = [random.choice(range(x)) for _ in range(numInSecond)]
            newData = [data[item] for item in sorted(newIndex)]
        elif x > numInSecond:
            newIndex = random.sample(range(x), numInSecond)
            newData = [data[item] for item in sorted(newIndex)]
        else:
            newData = data
        #print(newData)
        #for i in newData:
        #    processApplication(i)
        #saveData(newData)

def saveData(data):
    for i in data:
        global csvfile
        csv.writer(csvfile).writerow(i)
        #processApplication(i)


def on_message(client, userdata, message):
    global numInSecond
    global seconds
    global data
    global csvfile2
    global secondCounter
    if (seconds == -1):
        seconds = time.time()
    if str(message.payload)[2]=="T" :
        #print("Ignore message!")
        return 0
    if str(message.payload)[2]=="D" :
        #print("Ignore message!")
        return 0


    if str(message.payload)[2]=="C":
        print(str(message.payload)[2:-1])

        text=str(message.payload)[2:-1].split()
        currentTime = time.time() - seconds
        newrow = [currentTime]
        newrow.append(text[2])
        newrow.append(text[4])
        print(newrow)
        csv.writer(csvfile2).writerow(newrow)
        return 0
    #print ("Message received: " + str(message.payload))
    context = str(message.payload)[2:-1].split()





    currentTime=time.time() - seconds
    newrow = [currentTime]
    newrow.extend(context)

    if (currentTime<(secondCounter+0.99)):
        data.append(newrow)
    elif (currentTime>=(secondCounter+0.99) ):
        secondCounter+=1
        padding(data)
        data=[]







    global csvfile
    global gravity

    alpha=0.2

    gravity[0] = alpha * gravity[0] + (1 - alpha) * float(context[1])
    gravity[1] = alpha * gravity[1] + (1 - alpha) * float(context[2])
    gravity[2] = alpha * gravity[2] + (1 - alpha) * float(context[3])

    #print(gravity)
    #csv.writer(csvfile).writerow(gravity)
    

    #check gesture
    global init
    global stopThread
    pendingTime = 0.2
    checkResult = checkSatisfied(gravity)
    currentTime = time.time()

    global Pending, lastSwitchTime, Switch

    if not (init):
        Switch = checkResult
        print("Command {}".format(Switch))
        Pending = False
        init = True
    else:
        # print (checkResult)
        # print(Switch,  checkResult)
        if (Switch != checkResult):
            if not (Pending):
                Pending = True
                lastSwitchTime = currentTime
            else:
                if (currentTime - lastSwitchTime) >= pendingTime:
                    Switch = checkResult
                    Pending = False
                    print("Command {}".format(Switch))
                    if (Switch):
                        stopThread=False
                        t = threading.Thread(target=target)
                        t.setDaemon(True)
                        t.start()
                    else:
                        stopThread=True

        else:
            if Pending:
                Pending = False


def on_subscribe(mosq, obj, mid, granted_qos):
    print("Subscribed OK")
    print(mosq, obj, mid, granted_qos)


def on_unsubscribe(mosq, obj, mid, granted_qos):
    print("Unsubscribed OK")


stopThread=False
threadRunning=False
numInSecond=20
data=[]
secondCounter=0
counter=0
sequence=np.zeros((100, 3))
init=False
Pending=False
Switch=True
standardData=np.array([-0.352390461,-0.019114219,0.93773655])
seconds=-1
gravity=np.array([0.0,0.0,0.981])
Connected = False  # global variable for the state of the connection
broker_address = "m23.cloudmqtt.com"  # Broker address
port = 13299  # Broker port
user = "frylvkng"  # Connection username
password = "WWqMi9zd5xEa"  # Connection password
global client
client = mqttClient.Client("Python")  # create new instance
client.username_pw_set(user, password=password)  # set username and password
client.on_connect = on_connect  # attach function to callback
client.on_message = on_message  # attach function to callback
client.on_subscribe = on_subscribe
client.on_unsubscribe=on_unsubscribe

client.connect(broker_address, port=port)  # connect to broker

client.loop_start()  # start the loop

while Connected != True:  # Wait for connection
    time.sleep(0.1)

client.subscribe("python/test")
csvfile= open("test.csv","w")
csvfile2= open("reading.csv","w")

title=["time","index","x","y","z"]
csv.writer(csvfile).writerow(title)
title2=["time", "ECO2","TVOC"]
csv.writer(csvfile2).writerow(title2)
#client.loop_forever()
try:
    while True:
        time.sleep(0.01)

except KeyboardInterrupt:
    print("exiting",client.disconnect(),client.loop_stop())