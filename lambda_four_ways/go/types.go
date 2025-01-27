################################################################################
#
# MIT No Attribution
#
# Copyright Chariot Solutions
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################

package main

import (
    "fmt"
)


// this is heavily abridged from the actual event, and contains only those fields that we use
type Event struct {
    HttpMethod      *string                 `json:"httpMethod"`
    RequestPath     *string                 `json:"path"`
    PathParameters  *map[string]string      `json:"pathParameters"`
    Body            *string                 `json:"body"`
    IsBase64Encoded *bool                   `json:"isBase64Encoded"`
}


type Response struct {
    StatusCode          string                  `json:"statusCode"`
    Headers             map[string]string       `json:"headers"`
    IsBase64Encoded     bool                    `json:"isBase64Encoded"`
    Body                string                  `json:"body"`
}


func (e Event) String() string {
    return fmt.Sprintf("%v %v", *e.HttpMethod, *e.RequestPath)
}
