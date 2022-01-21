var AWS = require('aws-sdk');

var STS = new AWS.STS();
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
