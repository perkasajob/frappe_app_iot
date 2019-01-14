const getNotification = (clientId, username) => JSON.stringify({ clientId, username });

const validateClientConnected = (client) => {
    if (!client) {
        throw new Error("Client is not connected yet. Call client.connect() first!");
    }
};


var RealtimeClient = (clientId, username) => {
    const options = {
        will: {
            topic: LAST_WILL_TOPIC,
            payload: getNotification(clientId, username),
        }
    };
    let client = null;
    const clientWrapper = {};


    clientWrapper.connect = () => {
        return frappe.call({
            method: "iot.iot.getWebsocket",
            callback: function(res) {
                if(typeof res.message.url !== 'undefined'){
                    client  = mqtt.connect(res.message.url)
                    client.on('message', function (topic, message) {
                        // message is Buffer
                        console.log(message.toString())
                        // client.end()
                    })
                    client.on('connect', () => {
                        console.log('Connected to AWS IoT Broker');
                        client.subscribe(MESSAGE_TOPIC);
                        client.subscribe(CLIENT_CONNECTED);
                        client.subscribe(CLIENT_DISCONNECTED);
                        const connectNotification = getNotification(clientId, username);
                        client.publish(CLIENT_CONNECTED, connectNotification);
                        console.log('Sent message: ${CLIENT_CONNECTED} - ${connectNotification}');
                    });
                    client.on('close', () => {
                        console.log('Connection to AWS IoT Broker closed');
                        client.end();
                    });
                }
            }
        });
    }
    clientWrapper.onConnect = (callback) => {
        validateClientConnected(client)
        console.log("We are connected")
        client.on('connect', callback);
        return clientWrapper;
    };

    clientWrapper.onDisconnect = (callback) => {
        validateClientConnected(client)
        client.on('close', callback);
        return clientWrapper;
    };
    clientWrapper.onMessageReceived = (callback) => {
        validateClientConnected(client)
        client.on('message', (topic, message) => {
            console.log('Received message: ${topic} - ${message}');
            callback(topic, JSON.parse(message.toString('utf8')));
        });
        return clientWrapper;
    };
    clientWrapper.sendMessage = (message) => {
        validateClientConnected(client)
        client.publish(MESSAGE_TOPIC, JSON.stringify(message));
        console.log('Sent message: ${MESSAGE_TOPIC} - ${JSON.stringify(message)}');
        return clientWrapper;
    };
return clientWrapper;

};