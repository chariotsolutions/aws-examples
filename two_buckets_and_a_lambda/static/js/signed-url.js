/**
 *  This code retrieves a signed URL from the server and uses it to upload a file.
 */

const signedUrlUpload = (function() {

    const rootUrl = window.location.href.replace(/[^/]*$/, "");
    const queryUrl = rootUrl + "api/signedurl";

    async function requestSignedUrl(fileName, fileType) {
        console.log("requesting URL for " + fileName);
        const request = {
            method: 'POST',
            cache: 'no-cache',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                key: fileName,
                type: fileType
            })
        };
        const response = await fetch(queryUrl, request);
        if (response.ok) {
            content = await response.json();
            return content.url;
        }
        else {
            console.log("failed to retrieve signed URL: " + response.status)
        }
    }

    async function loadFileContent(selectedFile) {
        console.log("retrieving content for " + selectedFile.name);
        return new Promise(function(success, failure) {
            const reader = new FileReader();
            reader.onload = (e) => success(e.target.result);
            reader.onabort = failure;
            reader.readAsArrayBuffer(selectedFile);
        });
    }

    async function uploadFile(fileName, fileType, content, url) {
        console.log("uploading " + fileName);
        const request = {
            method: 'PUT',
            mode: 'cors',
            cache: 'no-cache',
            headers: {
                'Content-Type': fileType
            },
            body: content
        };
        const response = await fetch(url, request);
        console.log("upload status: " + response.status);
    }

    return async function() {
        const selectedFile = document.getElementById('fileselector').files[0];
        if (typeof selectedFile == 'undefined') {
            alert("Choose a file first");
            return;
        }

        const fileName = selectedFile.name;
        const fileType = selectedFile.type || "application/x-octet-stream";
        const url = await requestSignedUrl(fileName, fileType);
        const content = await loadFileContent(selectedFile);
        if (url && content) {
            await uploadFile(fileName, fileType, content, url);
            alert("upload via signed URL complete");
        }
    }

})();

