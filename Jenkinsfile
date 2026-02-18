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

    stage('Docker - Build Image') {
      steps {
        sh '''
          set -euo pipefail
          GIT_SHA=$(git rev-parse --short HEAD)
          echo "$GIT_SHA" > .git_sha
          docker buildx build --load -t fastapi-demo:${GIT_SHA} .
          docker images | grep fastapi-demo | head -n 5
        '''
      }
    }

    stage('Supply Chain - Generate SBOM (syft)') {
      steps {
        sh '''
        set -euo pipefail
        mkdir -p reports
        GIT_SHA=$(cat .git_sha)

        # Generate SBOM for the built image
        docker run --rm \
            --volumes-from jenkins \
            -v /var/run/docker.sock:/var/run/docker.sock \
            anchore/syft:v1.10.0 \
            fastapi-demo:${GIT_SHA} \
            -o cyclonedx-json > reports/sbom-${GIT_SHA}.cdx.json

        ls -la reports | grep sbom || true
        '''
      }
      post {
        always {
        archiveArtifacts artifacts: 'reports/sbom-*.cdx.json', fingerprint: true
        }
      }
    }

    stage('Security - Container Image Scan (trivy)') {
      steps {
        sh '''
          set -euo pipefail
          mkdir -p reports .trivycache
          GIT_SHA=$(cat .git_sha)

          docker run --rm \
            --volumes-from jenkins \
            -w "$WORKSPACE" \
            -v /var/run/docker.sock:/var/run/docker.sock \
            aquasec/trivy:latest \
            image \
            --scanners vuln \
            --pkg-types os,library \
            --severity HIGH,CRITICAL \
            --ignore-unfixed \
            --exit-code 1 \
            --cache-dir .trivycache \
            --format sarif \
            --output "reports/trivy-${GIT_SHA}.sarif" \
            "fastapi-demo:${GIT_SHA}"

          ls -la reports
        '''
      }
      post {
        always {
          archiveArtifacts artifacts: 'reports/trivy-*.sarif', fingerprint: true, allowEmptyArchive: true
        }
      }
    }
    
    stage('Publish - Push Image to GHCR') {
      when {
        expression { env.GIT_BRANCH == 'origin/main' }
      }
      environment {
        REGISTRY   = 'ghcr.io'
        IMAGE_REPO = 'ghcr.io/teeyoh/fastapi'
        GH_OWNER   = 'Teeyoh'
        GH_REPO    = 'FastAPI'
      }
      steps {
        withCredentials([
          string(credentialsId: 'gh_app_id', variable: 'GH_APP_ID'),
          file(credentialsId: 'gh_app_private_key', variable: 'GH_APP_KEYFILE')
        ]) {
          sh '''
            set -euo pipefail
            GIT_SHA=$(cat .git_sha)

            GH_TOKEN=$(docker run --rm \
              --volumes-from jenkins \
              -v /var/run/docker.sock:/var/run/docker.sock \
              -w /var/jenkins_home/workspace/fastapi-cicd \
              -e GH_APP_ID="$GH_APP_ID" \
              -e GH_APP_KEYFILE="$GH_APP_KEYFILE" \
              -e GH_OWNER="$GH_OWNER" \
              -e GH_REPO="$GH_REPO" \
              python:3.12-slim bash -lc "set -euo pipefail
    pip -q install pyjwt cryptography >/dev/null
    cat > /tmp/gh_app_token.py <<'PY'
    import os, time, json, subprocess
    import jwt

    app_id = os.environ['GH_APP_ID']
    key_path = os.environ['GH_APP_KEYFILE']
    owner = os.environ['GH_OWNER']
    repo  = os.environ['GH_REPO']

    with open(key_path, 'rb') as f:
        private_key = f.read()

    now = int(time.time())
    payload = {'iat': now - 30, 'exp': now + 9*60, 'iss': app_id}
    app_jwt = jwt.encode(payload, private_key, algorithm='RS256')

    headers = [
        '-H', f'Authorization: Bearer {app_jwt}',
        '-H', 'Accept: application/vnd.github+json',
    ]

    def curl_json(cmd):
        out = subprocess.check_output(cmd)
        return json.loads(out.decode('utf-8'))

    inst = curl_json(['curl', '-sS'] + headers + [f'https://api.github.com/repos/{owner}/{repo}/installation'])
    inst_id = inst['id']

    tok = curl_json(['curl', '-sS', '-X', 'POST'] + headers + [f'https://api.github.com/app/installations/{inst_id}/access_tokens'])
    print(tok['token'])
    PY
    python /tmp/gh_app_token.py")

            # Sanity check token non-empty (won't print token)
            test -n "$GH_TOKEN"

            echo "$GH_TOKEN" | docker login "$REGISTRY" -u teeyoh --password-stdin

            docker tag "fastapi-demo:${GIT_SHA}" "${IMAGE_REPO}:${GIT_SHA}"
            docker tag "fastapi-demo:${GIT_SHA}" "${IMAGE_REPO}:main"

            docker push "${IMAGE_REPO}:${GIT_SHA}"
            docker push "${IMAGE_REPO}:main"

            docker logout "$REGISTRY"
          '''
        }
      }
    }
  }
}
