/**
 *  This code retrieves credentials from the service and uses them with the
 *  AWS SDK to perform a (potential) multi-part upload.
 */

const credentialsUpload = (function() {

    const rootUrl = window.location.href.replace(/[^/]*$/, "");
    const queryUrl = rootUrl + "api/credentials";

    async function requestCredentials(selectedFile) {
        console.log("requesting credentials for " + selectedFile.name);
        const request = {
            method: 'POST',
            cache: 'no-cache',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                key: selectedFile.name,
            })
        };
        let response = await fetch(queryUrl, request);
        if (response.ok) {
            return response.json();
        }
        else {
            console.log("failed to retrieve credentials: " + response.status);
        }
    }

    async function uploadFile(selectedFile, accessKeyId, secretAccessKey, sessionToken, region, bucket) {
        AWS.config.region = region; 
        AWS.config.credentials = new AWS.Credentials(accessKeyId, secretAccessKey, sessionToken);
        const s3 = new AWS.S3();

        console.log("uploading " + selectedFile.name);
        const params = {
          Bucket:       bucket, 
          Key:          selectedFile.name,
          ContentType:  selectedFile.type,
          Body:         selectedFile
         };
        let upload = new AWS.S3.ManagedUpload({ params: params });
        upload.on('httpUploadProgress', function(evt) {
            console.log("uploaded " + evt.loaded + " of " + evt.total + " bytes for " + selectedFile.name);
        });
        return upload.promise();
    }

    return async function() {
        let selectedFile = document.getElementById('fileselector').files[0];
        let creds = await requestCredentials(selectedFile);
        if (creds) {
            await uploadFile(selectedFile, creds.access_key, creds.secret_key, creds.session_token, creds.region, creds.bucket);
            alert("upload complete");
        }
    }

})();
