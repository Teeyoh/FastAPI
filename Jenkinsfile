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

    stage('Debug Workspace') {
      steps {
        sh '''
          echo "Jenkins workspace: $WORKSPACE"
          ls -la
          find . -maxdepth 3 -type f | sed -n '1,200p'
          docker run --rm -v "$WORKSPACE:/work" -w /work python:3.12-slim sh -lc '
            echo "Inside container, pwd: $(pwd)";
            ls -la;
            echo "Top files:"; find . -maxdepth 3 -type f | sed -n "1,200p";
            echo "Python files:"; find . -name "*.py" -maxdepth 5 -print;
            echo "Tests:"; find . -path "./tests/*" -type f -maxdepth 3 -print;
          '
        '''
      }
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
        '''
      }
    }
  }
}
