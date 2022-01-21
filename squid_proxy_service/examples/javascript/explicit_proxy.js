var AWS = require('aws-sdk');

var config = {
    "sslEnabled": true,
    "httpOptions": {
        "proxy": "http://squid_proxy.internal:3128"
    }
}

var STS = new AWS.STS(config);
STS.getCallerIdentity({}, function(err, data) {
    if (err) {
        console.log("error: " + err)
    }
    else {
        console.log("User:    " + data.UserId)
        console.log("Account: " + data.Account)
        console.log("Arn:     " + data.Arn)
    }
});
