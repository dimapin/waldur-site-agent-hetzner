{{- define "waldur-site-agent-hetzner.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- define "waldur-site-agent-hetzner.fullname" -}}
{{- if .Values.fullnameOverride }}{{ .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}{{ else }}{{ printf "%s-%s" .Release.Name (include "waldur-site-agent-hetzner.name" .) | trunc 63 | trimSuffix "-" }}{{ end }}
{{- end }}
{{- define "waldur-site-agent-hetzner.labels" -}}
app.kubernetes.io/name: {{ include "waldur-site-agent-hetzner.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
