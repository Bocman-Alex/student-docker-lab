pipeline {
    agent any

    parameters {
        string(name: 'STUDENT_NAME', defaultValue: 'Your Name', description: 'Student name')
        choice(name: 'ENVIRONMENT', choices: ['dev', 'staging', 'production'], description: 'Environment')
        booleanParam(name: 'RUN_TESTS', defaultValue: true, description: 'Run unit tests')
    }

    environment {
        DOCKER_REGISTRY = 'docker.io'
        DOCKER_USER = 'botsman01'   // замените на ваш логин
        DOCKER_IMAGE_API = "${DOCKER_REGISTRY}/${DOCKER_USER}/student-app-api:${BUILD_NUMBER}"
        DOCKER_IMAGE_NGINX = "${DOCKER_REGISTRY}/${DOCKER_USER}/student-app-nginx:${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Unit Tests') {
            when {
                expression { params.RUN_TESTS }
            }
            steps {
                sh '''
                    cd api
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                    python -m unittest test_app.py -v
                '''
            }
        }

        stage('Build Docker Images') {
            steps {
                script {
                    docker.build("${DOCKER_IMAGE_API}", "./api")
                    docker.build("${DOCKER_IMAGE_NGINX}", "./nginx")
                }
            }
        }

        stage('Push to Registry') {
            steps {
                script {
                    docker.withRegistry("https://${DOCKER_REGISTRY}", 'docker-hub-credentials') {
                        docker.image("${DOCKER_IMAGE_API}").push()
                        docker.image("${DOCKER_IMAGE_NGINX}").push()
                        docker.image("${DOCKER_IMAGE_API}").push("latest")
                        docker.image("${DOCKER_IMAGE_NGINX}").push("latest")
                    }
                }
            }
        }

        stage('Deploy to Dev') {
            when {
                expression { params.ENVIRONMENT == 'dev' }
            }
            steps {
                sh """
                    docker stop student-app-dev || true
                    docker rm student-app-dev || true
                    docker run -d --name student-app-dev -p 8081:80 ${DOCKER_IMAGE_NGINX}
                """
            }
        }

        stage('Deploy to Staging') {
            when {
                expression { params.ENVIRONMENT == 'staging' }
            }
            steps {
                sh """
                    cd ~/docker-lab-compose
                    docker compose down
                    docker compose up -d
                """
            }
        }

        stage('Approve Production') {
            when {
                expression { params.ENVIRONMENT == 'production' }
            }
            input {
                message "Deploy to production?"
                ok "Yes"
            }
            steps {
                echo "Production deployment approved"
            }
        }

        stage('Deploy to Production') {
            when {
                expression { params.ENVIRONMENT == 'production' }
            }
            steps {
                sh """
                    cd ~/docker-lab-compose
                    docker compose down
                    docker compose up -d
                """
            }
        }
    }

    post {
        success {
            echo 'Pipeline succeeded'
        }
        failure {
            echo 'Pipeline failed'
        }
    }
}
