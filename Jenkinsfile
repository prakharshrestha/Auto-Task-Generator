pipeline {
  agent any

  environment {
    DEPLOY_DIR = "/opt/Auto-Task-Generator"
    VENV_DIR   = "/opt/Auto-Task-Generator/venv"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Deploy code to /opt') {
      steps {
        sh '''
          set -euxo pipefail
          rsync -a --delete \
            --exclude ".git" \
            --exclude "venv" \
            --exclude "__pycache__" \
            ./ "${DEPLOY_DIR}/"
        '''
      }
    }

    stage('Install Dependencies (in /opt venv)') {
    options { timeout(time: 20, unit: 'MINUTES') }
    steps {
      sh '''
        set -euxo pipefail
        cd "${DEPLOY_DIR}"
        test -x venv/bin/python || /usr/bin/python3 -m venv venv
        ./venv/bin/pip install --upgrade pip
        ./venv/bin/pip install -r requirements.txt
      '''
    }
  }

    stage('Restart Application') {
      steps {
        sh 'sudo /usr/bin/systemctl restart autotask'
      }
    }

    stage('Verify') {
      steps {
        sh '''
          set -euxo pipefail
          sudo /usr/bin/systemctl is-active autotask
          curl -fsS http://127.0.0.1:8000/docs >/dev/null
        '''
      }
    }
  }
}
