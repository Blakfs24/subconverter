// main.go
package main

import (
	"fmt"
	"io"
	"os"
	"unsafe"
)

/*
#cgo LDFLAGS: -L../  -lsubconverter -static -lpcre2-8 -lyaml-cpp -lstdc++ -lm
#include <stdlib.h>

// 声明外部 C 函数
char* NodeToSingbox(const char* input, const char* delimiter);
*/
import "C"

func NodeToSingbox(input string, delimiter string) string {
	// Convert Go string to C string
	cInput := C.CString(input)
	defer C.free(unsafe.Pointer(cInput)) // Enasure to free Go memory allocated by C.CString
	cDelimiter := C.CString(delimiter)
	defer C.free(unsafe.Pointer(cDelimiter))

	// Call C++ function to process the string
	cOutput := C.NodeToSingbox(cInput, cDelimiter)
	if cOutput == nil {
		return ""
	}

	// Convert C string to Go string
	goOutput := C.GoString(cOutput)

	// release memory allocated by C++ code
	C.free(unsafe.Pointer(cOutput))

	return goOutput
}

func main() {
	goInput := "vmess://ew0KICAidiI6ICIyIiwNCiAgInBzIjogIlNDUDIiLA0KICAiYWRkIjogInd3dy5zbWNhY3JlLmdvdiIsDQogICJwb3J0IjogIjQ0MyIsDQogICJpZCI6ICIzY2M4ZTJkMi1lNGE0LTRkODctYzE2Yy1hOGZjNzAyOTZhN2IiLA0KICAiYWlkIjogIjAiLA0KICAic2N5IjogImF1dG8iLA0KICAibmV0IjogIndzIiwNCiAgInR5cGUiOiAibm9uZSIsDQogICJob3N0IjogImxhamlodWF3ZWkuY29tIiwNCiAgInBhdGgiOiAiLzNjYzhlMmQyIiwNCiAgInRscyI6ICJ0bHMiLA0KICAic25pIjogInd3dy5zbWNhY3JlLmdvdiIsDQogICJhbHBuIjogIiINCn0="
	out := NodeToSingbox(goInput, "link")
	fmt.Println(out)

	// goInput := "{\"type\":\"vmess\",\"tag\":\"SCP2\",\"server\":\"www.smcacre.gov\",\"server_port\":443,\"uuid\":\"3cc8e2d2-e4a4-4d87-c16c-a8fc70296a7b\",\"alter_id\":0,\"security\":\"auto\",\"transport\":{\"type\":\"ws\",\"path\":\"/3cc8e2d2\",\"headers\":{\"Host\":\"lajihuawei.com\"}},\"tls\":{\"enabled\":true,\"server_name\":\"www.smcacre.gov\",\"insecure\":false}}"
	path := "/workspaces/singtools_private/config.yaml"
	// os.ReadFile(path)
	file, err := os.Open(path)
	if err != nil {
		fmt.Println(err)
	}
	defer file.Close()
	data, err := io.ReadAll(file)
	if err != nil {
		fmt.Println(err)
	}
	goInput = string(data)
	fmt.Println(goInput[:100])
	out = NodeToSingbox(goInput, "multi")
	fmt.Println(out)
}
