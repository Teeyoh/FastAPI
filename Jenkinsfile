pipeline {
  agent any

  options {
    timestamps()
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Python - Lint & Format Check') {
      steps {
        sh '''
          python -V
          pip -V
          pip install -U pip
          pip install ruff black
          ruff check .
          black --check .
        '''
      }
    }

    stage ('Python - Tests') {
      steps {
        sh '''
          pip install -U pytest httpx fastapi "uvicorn[standard]"
          pytest
        '''
      }
    }

    stage ('Docker - Build Image') {
      steps {
        sh '''
          GIT_SHA=$(git rev-parse --short HEAD)
          docker build -t fastapi-demo:${GIT_SHA}
        '''
      }
    }
  }  
}