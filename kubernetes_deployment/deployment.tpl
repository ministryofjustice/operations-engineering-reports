apiVersion: apps/v1
kind: Deployment
metadata:
  name: operations-engineering-reports
  namespace: operations-engineering
spec:
  replicas: 3
  selector:
    matchLabels:
      app: operations-engineering-reports-app
  template:
    metadata:
      labels:
        app: operations-engineering-reports-app
    spec:
      containers:
        - name: operations-engineering-reports
          image: 754256621582.dkr.ecr.eu-west-2.amazonaws.com/${ECR_NAME}:${IMAGE_TAG}
          env:
            - name: FLASK_DEBUG
              value: "false"
            - name: API_KEY
              valueFrom:
                secretKeyRef:
                  name: operations-engineering-reports-api-key
                  key: token
            - name: DYNAMODB_REGION
              value: "eu-west-2"
            - name: DYNAMODB_ACCESS_KEY_ID
              valueFrom:
                secretKeyRef:
                  name: opseng-reports-table
                  key: access_key_id
            - name: DYNAMODB_SECRET_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: opseng-reports-table
                  key: secret_access_key
            - name: DYNAMODB_TABLE_NAME
              valueFrom:
                secretKeyRef:
                  name: opseng-reports-table
                  key: table_name
            - name: AUTH0_CLIENT_ID
              valueFrom:
                secretKeyRef:
                  name: opseng-reports-table
                  key: auth0_client_id
            - name: AUTH0_CLIENT_SECRET
              valueFrom:
                secretKeyRef:
                  name: opseng-reports-table
                  key: auth0_secret
            - name: AUTH0_DOMAIN
              value: "operations-engineering.eu.auth0.com"
            - name: APP_SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: opseng-reports-table
                  key: flask_app_secret
            - name: ENCRYPTION_KEY
              valueFrom:
                secretKeyRef:
                  name: opseng-reports-table
                  key: opseng_reports_encrypt_key
          ports:
          - containerPort: 4567
