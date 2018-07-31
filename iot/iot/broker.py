from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient, AWSIoTMQTTShadowClient
import logging
import time, threading
import argparse, pdb, json

from random import randint

# Shadow JSON schema:
#
# Name: Bot
# {
#	"state": {
#		"desired":{
#			"property":<INT VALUE>
#		}
#	}
# }

timeOffset = 1483228800 # 2017 jan 01


class ServerConnection:
# Custom MQTT message callback
    def customCallback(self, client, userdata, message):
        print("Received a new message: ")
        print(message.payload)
        print("from topic: ")
        print(message.topic)
        print("--------------\n\n")

        self.callbackFcn(message.payload) # this must be adapted to message structure

    def customCallback2(self, client, userdata, message):
        print("Received a new message: ")
        print(message.payload)
        print("from topic: ")
        print(message.topic)
        print("--------------\n\n")

        self.callbackFcn2(message) # this must be adapted to message structure

    def customShadowCallback_Update(self, payload, responseStatus, token):
        # payload is a JSON string ready to be parsed using json.loads(...)
        # in both Py2.x and Py3.x
        if responseStatus == "timeout":
            print("Update request " + token + " time out!")
        if responseStatus == "accepted":
            payloadDict = json.loads(payload)
            print("~~~~~~~~~~~~~~~~~~~~~~~")
            print("Update request with token: " + token + " accepted!")
            print("hwinputs: " + str(payloadDict["state"]["reported"]["hwinputs"]))
            print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
        if responseStatus == "rejected":
            print("Update request " + token + " rejected!")

    def customShadowCallback_Delete(self, payload, responseStatus, token):
        if responseStatus == "timeout":
            print("Delete request " + token + " time out!")
        if responseStatus == "accepted":
            print("~~~~~~~~~~~~~~~~~~~~~~~")
            print("Delete request with token: " + token + " accepted!")
            print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
        if responseStatus == "rejected":
            print("Delete request " + token + " rejected!")

    def customShadowCallback_Delta(payload, responseStatus, token):
        # payload is a JSON string ready to be parsed using json.loads(...)
        # in both Py2.x and Py3.x
        print(responseStatus)
        payloadDict = json.loads(payload)
        print("++++++++DELTA++++++++++")
        print("property: " + str(payloadDict["state"]["property"]))
        print("version: " + str(payloadDict["version"]))
        print("+++++++++++++++++++++++\n\n")

    def publishValue(self, id = None, topic = None, **val):
        current_milli_time = lambda: int(round(time.time() * 1000))
        val = { 'name' : self.clientId,\
                'data' : val,\
                'id': str(current_milli_time()) if id is None else id \
        }
        print("publish: " + json.dumps(val))
        self.myAWSIoTMQTTClient.publish(self.topic if topic is None else topic, json.dumps(val), 1)

    def publishValue(self, val, id = None, topic = None):
        current_milli_time = lambda: int(round((time.time()-timeOffset) * 1000))
        val.update({ 'name' : self.clientId })
        print("publish: " + json.dumps(val))
        self.myAWSIoTMQTTClient.publish(self.topic if topic is None else topic, json.dumps(val), 0)


    def bindResponseMsg(self, f):
        self.callbackFcn = f

    def bindResponseMsg2(self, f):
        self.callbackFcn2 = f

    def timecb(self):

        if self.callbackFcn != None:
            self.callbackFcn(randint(0, 9))

        threading.Timer(2, self.timecb).start()

    def shadowUpdate(self, JSONPayload):
        self.deviceShadowHandler.shadowUpdate(JSONPayload, self.customShadowCallback_Update, 5)

    def shadowDelete(self, JSONPayload):
        # Delete shadow JSON doc
        self.deviceShadowHandler.shadowDelete(self.customShadowCallback_Delete, 5)

    def listenDelta(self):
        # Listen on deltas
        self.deviceShadowHandler.shadowRegisterDeltaCallback(customShadowCallback_Delta)


    def __init__(self, host, rootCAPath, clientId, topic, thingName, is_shadow):
        self.callbackFcn = None
        self.clientId = str(clientId)
        self.thingName = str(thingName)
        self.topic = str(topic)

        # Configure logging
        logger = logging.getLogger("AWSIoTPythonSDK.core")
        logger.setLevel(logging.ERROR)
        streamHandler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        streamHandler.setFormatter(formatter)
        logger.addHandler(streamHandler)

        # Cognito auth
        # identityPoolID = cognitoIdentityPoolID
        # region = host.split('.')[2]
        # cognitoIdentityClient = boto3.client('cognito-identity', region_name=region)
        # identityPoolInfo = cognitoIdentityClient.describe_identity_pool(IdentityPoolId=identityPoolID)
        # print identityPoolInfo

        # temporaryIdentityId = cognitoIdentityClient.get_id(IdentityPoolId=identityPoolID)
        # identityID = temporaryIdentityId["IdentityId"]

        # temporaryCredentials = cognitoIdentityClient.get_credentials_for_identity(IdentityId=identityID)
        # AccessKeyId = temporaryCredentials["Credentials"]["AccessKeyId"]
        # SecretKey = temporaryCredentials["Credentials"]["SecretKey"]
        # SessionToken = temporaryCredentials["Credentials"]["SessionToken"]

        # Init AWSIoTMQTTClient
        if is_shadow :
            self.myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(clientId, useWebsocket=True)
            self.myAWSIoTMQTTShadowClient.configureEndpoint(host, 443)
            self.myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath)
            self.myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
            self.myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
            self.myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5)  # 5 sec
            self.myAWSIoTMQTTShadowClient.connect()

            # Create a deviceShadow with persistent subscription
            self.deviceShadowHandler = self.myAWSIoTMQTTShadowClient.createShadowHandlerWithName(self.thingName , True)
        else:
            self.myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId, useWebsocket=True)
            # AWSIoTMQTTClient configuration
            self.myAWSIoTMQTTClient.configureEndpoint(host, 443)
            self.myAWSIoTMQTTClient.configureCredentials(rootCAPath)
            # self.myAWSIoTMQTTClient.configureIAMCredentials(AccessKeyId, SecretKey, SessionToken)
            self.myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
            self.myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
            self.myAWSIoTMQTTClient.configureDrainingFrequency(5)  # Draining: 5 Hz
            self.myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
            self.myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec
            # Connect and subscribe to AWS IoT
            self.myAWSIoTMQTTClient.connect()
            self.myAWSIoTMQTTClient.subscribe(self.topic, 1, self.customCallback)

        time.sleep(2)
