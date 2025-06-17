package utils

import (
	networking "k8s.io/api/networking/v1"
)

// Variables for k8s contants... The k8s api structs often take pointers to
// strings or ints and we just want to specify a value. But &1 or &"Prefix" is
// not valid go, you can't take the address of a constant. So you end up making
// temporary variables to take the address of, and allocating unnecessarily.

var (
	True  bool = true
	False bool = false
)

var (
	Int32_1 int32 = 1
	Int32_2 int32 = 2
	Int32_3 int32 = 3

	Int32_0o600 int32 = 0o600
	Int32_0o644 int32 = 0o644
	Int32_0o755 int32 = 0o755

	Int64_0  int64 = 0
	Int64_10 int64 = 10
)

var (
	StrNginx string = "nginx"
)

var (
	PathTypePrefix networking.PathType = networking.PathTypePrefix
)

var (
	VolumedNodeSelector = map[string]string{"k8s.datacoves.com/nodegroup-kind": "volumed"}
	GeneralNodeSelector = map[string]string{"k8s.datacoves.com/nodegroup-kind": "general"}
)
