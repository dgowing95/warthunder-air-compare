{{- define "warthunder-air-compare.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "warthunder-air-compare.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s" (include "warthunder-air-compare.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "warthunder-air-compare.labels" -}}
app.kubernetes.io/name: {{ include "warthunder-air-compare.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" }}
{{- end -}}

{{- define "warthunder-air-compare.selectorLabels" -}}
app.kubernetes.io/name: {{ include "warthunder-air-compare.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
