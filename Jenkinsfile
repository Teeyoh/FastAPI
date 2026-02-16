pipeline {
  agent any

  options {
    timestamps()
  }

  environment {
    PY_IMAGE = "python:3.12-slim"
    TRIVY_IMAGE = "aquasec/trivy:latest"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Security - Secret Scan (gitleaks)') {
      steps {
        sh '''
        mkdir -p reports
        GIT_SHA=$(cat .git_sha 2>/dev/null || git rev-parse --short HEAD)

        docker run --rm \
            --volumes-from jenkins \
            -w "$WORKSPACE" \
            zricethezav/gitleaks:latest \
            detect --source . \
            --report-format sarif \
            --report-path reports/gitleaks-${GIT_SHA}.sarif \
            --exit-code 1
        '''
      }
      post {
        always {
        archiveArtifacts artifacts: 'reports/gitleaks-*.sarif', fingerprint: true
        }
      }
    }


    stage('Lint & Format Check (containerized)') {
      steps {
        sh '''
          docker run --rm \
            --volumes-from jenkins \
            -w "$WORKSPACE" \
            $PY_IMAGE \
            sh -lc "pip install -U pip ruff black && ruff check . && black --check ."
        '''
      }
    }

    stage('Tests (containerized)') {
      steps {
        sh '''
          docker run --rm \
            --volumes-from jenkins \
            -w "$WORKSPACE" \
            $PY_IMAGE \
            sh -lc "pip install -U pip pytest httpx fastapi 'uvicorn[standard]' && pytest"
        '''
      }
    }

    stage('Docker - Build Image') {
      steps {
        sh '''
          GIT_SHA=$(git rev-parse --short HEAD)
          echo "$GIT_SHA" > .git_sha
          docker build -t fastapi-demo:${GIT_SHA} .
        '''
      }
    }


    stage('Security - Python Dependency Audit (pip-audit)') {
      steps {
        sh '''
          mkdir -p reports
          GIT_SHA=$(cat .git_sha)

          docker run --rm \
            --volumes-from jenkins \
            -w "$WORKSPACE" \
            $PY_IMAGE \
            sh -lc "pip install -U pip pip-audit && pip-audit -r requirements.txt -f json > reports/pip-audit-${GIT_SHA}.json"
        '''
      }
      post {
        always {
          archiveArtifacts artifacts: 'reports/pip-audit-*.json', fingerprint: true
        }
      }
    }

    stage('Security - Container Image Scan (trivy)') {
      steps {
        sh '''
          mkdir -p reports
          GIT_SHA=$(cat .git_sha)

          docker run --rm \
            --volumes-from jenkins \
            -w "$WORKSPACE" \
            -v /var/run/docker.sock:/var/run/docker.sock \
            aquasec/trivy:latest \
            image --scanners vuln \
            --format sarif --output reports/trivy-${GIT_SHA}.sarif \
            fastapi-demo:${GIT_SHA}

          ls -la reports
        '''
      }
      post {
        always {
          archiveArtifacts artifacts: 'reports/trivy-*.sarif', fingerprint: true, allowEmptyArchive: false
        }
      }
    }
  }
}
