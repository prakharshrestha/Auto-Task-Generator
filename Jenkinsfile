pipeline {
  agent any

  options {
    skipDefaultCheckout(true)
    timestamps()
  }

  environment {
    COMPOSE_FILE = "docker-compose.yml"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Build') {
      steps {
        sh '''
          set -euxo pipefail
          docker compose -f "${COMPOSE_FILE}" build --no-cache
        '''
      }
    }

    stage('Deploy') {
      steps {
        sh '''
          set -euxo pipefail
          docker compose -f "${COMPOSE_FILE}" up -d
          docker image prune -f || true
        '''
      }
    }

    stage('Verify') {
      steps {
        sh '''
          set -euxo pipefail

          # Wait for backend docs
          for i in $(seq 1 30); do
            if curl -fsS http://127.0.0.1:8000/docs >/dev/null; then
              echo "Backend is responding"
              exit 0
            fi
            echo "Waiting for backend... ($i/30)"
            sleep 2
          done

          echo "Backend did not become ready"
          docker ps
          docker logs auto-task-backend --tail 200 || true
          exit 1
        '''
      }
    }
  }
}
