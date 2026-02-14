pipeline {
  agent any

  options { timestamps() }

  environment {
    PY_IMAGE = "python:3.12-slim"
  }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Lint & Format Check (containerized)') {
      steps {
        sh '''
          docker run --rm \
            --volumes-from jenkins \
            -w "$WORKSPACE" \
            python:3.12-slim \
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
            python:3.12-slim \
            sh -lc "pip install -U pip pytest httpx fastapi 'uvicorn[standard]' && pytest"
        '''
      }
    }


    stage('Docker - Build Image') {
      steps {
        sh '''
          GIT_SHA=$(git rev-parse --short HEAD)
          docker build -t fastapi-demo:${GIT_SHA} .
          export DOCKER_BUILDKIT=1
        '''
      }
    }
  }
}
