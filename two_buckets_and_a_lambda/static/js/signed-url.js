/**
 *  This code retrieves a signed URL from the server and uses it to upload a file.
 */

const signedUrlUpload = (function() {

    const rootUrl = window.location.href.replace(/[^/]*$/, "");
    const queryUrl = rootUrl + "api/signedurl";

    async function requestSignedUrl(selectedFile) {
        console.log("requesting URL for " + selectedFile.name);
        const request = {
            method: 'POST',
            cache: 'no-cache',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                key: selectedFile.name,
                type: selectedFile.type
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
            reader.readAsBinaryString(selectedFile);
        });
    }

    async function uploadFile(selectedFile, content, url) {
        console.log("uploading " + selectedFile.name);
        const request = {
            method: 'PUT',
            mode: 'cors',
            cache: 'no-cache',
            headers: {
                'Content-Type': selectedFile.type
            },
            body: content
        };
        const response = await fetch(url, request);
        console.log("upload status: " + response.status);
    }

    return async function() {
        console.log('foo!');
        alert('bar');
        
        const selectedFile = document.getElementById('fileselector').files[0];
        const url = await requestSignedUrl(selectedFile);
        const content = await loadFileContent(selectedFile);
        if (url && content) {
            await uploadFile(selectedFile, content, url);
            alert("upload complete");
        }
    }

})();

