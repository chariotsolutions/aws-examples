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
