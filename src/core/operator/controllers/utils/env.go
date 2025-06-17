package utils

import (
	core "k8s.io/api/core/v1"
)

// []core.EnvVar wrapper type with helper methods to specify envs more succinctly.
type Env []core.EnvVar

func (e Env) Set(name, value string) Env {
	for i, v := range e {
		if v.Name == name {
			e[i] = core.EnvVar{Name: name, Value: value}
			return e
		}
	}
	return append(e, core.EnvVar{Name: name, Value: value})
}

func (e Env) AddFromConfigMap(configMapName string, vars ...string) Env {
	for _, name := range vars {
		e = append(e, core.EnvVar{
			Name: name,
			ValueFrom: &core.EnvVarSource{
				ConfigMapKeyRef: &core.ConfigMapKeySelector{
					LocalObjectReference: core.LocalObjectReference{Name: configMapName},
					Key:                  name,
				},
			},
		})
	}
	return e
}

func (e Env) AddFromSecret(secretName string, vars ...string) Env {
	for _, name := range vars {
		e = append(e, core.EnvVar{
			Name: name,
			ValueFrom: &core.EnvVarSource{
				SecretKeyRef: &core.SecretKeySelector{
					LocalObjectReference: core.LocalObjectReference{Name: secretName},
					Key:                  name,
				},
			},
		})
	}
	return e
}

func (e Env) RenameFromConfigMap(configMapName string, vars [][2]string) Env {
	for _, kv := range vars {
		k, v := kv[0], kv[1]
		e = append(e, core.EnvVar{
			Name: k,
			ValueFrom: &core.EnvVarSource{
				ConfigMapKeyRef: &core.ConfigMapKeySelector{
					LocalObjectReference: core.LocalObjectReference{Name: configMapName},
					Key:                  v,
				},
			},
		})
	}
	return e
}

func (e Env) RenameFromSecret(secretName string, vars [][2]string) Env {
	for _, kv := range vars {
		k, v := kv[0], kv[1]
		e = append(e, core.EnvVar{
			Name: k,
			ValueFrom: &core.EnvVarSource{
				SecretKeyRef: &core.SecretKeySelector{
					LocalObjectReference: core.LocalObjectReference{Name: secretName},
					Key:                  v,
				},
			},
		})
	}
	return e
}
