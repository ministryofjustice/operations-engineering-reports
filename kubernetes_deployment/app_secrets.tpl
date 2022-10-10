apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: operations-engineering
type: Opaque
data:
  AUTH0_CLIENT_ID: ${AUTH0_CLIENT_ID}
  AUTH0_CLIENT_SECRET: ${AUTH0_CLIENT_SECRET}
  APP_SECRET_KEY: ${FLASK_APP_SECRET}
  ENCRYPTION_KEY: ${OPS_ENG_REPORTS_ENCRYPT_KEY}
  API_KEY: {OPERATIONS_ENGINEERING_REPORTS_API_KEY}