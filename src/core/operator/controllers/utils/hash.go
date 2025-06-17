package utils

import (
	"context"
	"crypto/sha256"
	"fmt"
	"sort"

	"sigs.k8s.io/controller-runtime/pkg/client"

	core "k8s.io/api/core/v1"
)

func HashForName(data []byte) string {
	return fmt.Sprintf("%x", sha256.Sum256(data))[:10]
}

func HashSecret(secret *core.Secret) string {
	h := sha256.New()

	// Iterating over go hashmaps yields items in random order, which changes the
	// sha. We need to sort them first.
	keys := []string{}
	for k, _ := range secret.Data {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, k := range keys {
		h.Write([]byte(k))
		h.Write(secret.Data[k])
	}

	keys = []string{}
	for k, _ := range secret.StringData {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, k := range keys {
		h.Write([]byte(k))
		h.Write([]byte(secret.StringData[k]))
	}

	return fmt.Sprintf("%x", h.Sum(nil))[:10]
}

func HashConfigMap(configMap *core.ConfigMap) string {
	h := sha256.New()

	// Iterating over go hashmaps yields items in random order, which changes the
	// sha. We need to sort them first.
	keys := []string{}
	for k, _ := range configMap.Data {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, k := range keys {
		h.Write([]byte(k))
		h.Write([]byte(configMap.Data[k]))
	}

	keys = []string{}
	for k, _ := range configMap.BinaryData {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, k := range keys {
		h.Write([]byte(k))
		h.Write(configMap.BinaryData[k])
	}

	return fmt.Sprintf("%x", h.Sum(nil))[:10]
}

func GetSecretHashed(ctx context.Context, c client.Client, key client.ObjectKey) (*core.Secret, error) {
	base := core.Secret{}
	err := c.Get(ctx, key, &base)
	if err != nil {
		return nil, err
	}
	secret := &core.Secret{}
	secret.TypeMeta = base.TypeMeta
	// Intentionally not copying most metadata.
	secret.Namespace = base.Namespace
	secret.Name = base.Name + "-" + HashSecret(&base)
	secret.Type = base.Type
	secret.Immutable = &True
	secret.Data = base.Data
	secret.StringData = base.StringData
	return secret, nil
}

func GetConfigMapHashed(ctx context.Context, c client.Client, key client.ObjectKey) (*core.ConfigMap, error) {
	base := core.ConfigMap{}
	err := c.Get(ctx, key, &base)
	if err != nil {
		return nil, err
	}
	configMap := &core.ConfigMap{}
	configMap.TypeMeta = base.TypeMeta
	// Intentionally not copying most metadata.
	configMap.Namespace = base.Namespace
	configMap.Name = base.Name + "-" + HashConfigMap(&base)
	configMap.Immutable = &True
	configMap.Data = base.Data
	configMap.BinaryData = base.BinaryData
	return configMap, nil
}
