pipeline {
  agent any

  options {
    skipDefaultCheckout(true)
    timestamps()
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Build images') {
      steps {
        sh '''
          set -euxo pipefail
          docker compose build
        '''
      }
    }
    stage('Create .env') {
      steps {
        withCredentials([file(credentialsId: 'auto-task-env', variable: 'ENVFILE')]) {
          sh '''
            set -euxo pipefail
            cp "$ENVFILE" .env
            chmod 600 .env
          '''
        }
      }
    }
    stage('Deploy') {
      steps {
        sh '''
          set -euxo pipefail
          docker compose up -d
        '''
      }
    }

    stage('Verify') {
      steps {
        sh '''
          set -euxo pipefail

          # backend readiness
          for i in $(seq 1 30); do
            if curl -fsS http://127.0.0.1:8000/docs >/dev/null; then
              echo "Backend is responding"
              exit 0
            fi
            echo "Waiting for backend... ($i/30)"
            sleep 2
          done

          docker ps
          docker logs auto-task-backend --tail 200 || true
          exit 1
        '''
      }
    }
  }

  post {
    always {
      sh 'docker compose ps || true'
    }
  }
}
