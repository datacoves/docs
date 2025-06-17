package main

import (
	"crypto/rand"
	"fmt"
	"os"
	"time"
)

func main() {
	fmt.Println("args", os.Args[1:])
	cmd := ""
	for i := 1; i < len(os.Args); i++ {
		switch os.Args[i] {
		case "upgrade", "uninstall":
			cmd = os.Args[i]
			break
		case "repo":
			if i+1 < len(os.Args) && os.Args[i+1] == "update" {
				cmd = "repo update"
			} else {
				cmd = "repo add"
			}
			break
		}
	}

	const MB = 1024 * 1024
	var allocBytes int
	var sleepSeconds int

	switch cmd {
	case "upgrade":
		sleepSeconds = 30
		allocBytes = 20 * MB
	case "uninstall":
		sleepSeconds = 10
		allocBytes = 20 * MB
	case "repo update":
		sleepSeconds = 7
		allocBytes = 2 * MB
	case "repo add":
		sleepSeconds = 1
		allocBytes = 1 * MB
	default:
		return
	}

	b := make([]byte, allocBytes)
	_, err := rand.Read(b)
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
	time.Sleep(time.Duration(sleepSeconds) * time.Second)

	checksum := uint32(0)
	for i := 0; i < allocBytes; i++ {
		checksum += uint32(b[i])
	}
	fmt.Println("done", checksum, os.Args[1:])
}
