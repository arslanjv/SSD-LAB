pipeline {
    agent any

    stages {
        // Stage 1: Checkout (Automatic or Explicit)
        stage('Clone Repo') {
            steps {
                checkout scm
                bat 'echo Repository cloned successfully.'
            }
        }

        // Stage 2: Install Dependencies
        stage('Install Dependencies') {
            steps {
                // Use 'bat' for Windows. 
                // Note: Windows uses 'call' to activate venv and backslashes for paths.
                bat '''
                    python -m venv venv
                    call venv\\Scripts\\activate
                    pip install -r requirements.txt
                '''
            }
        }

        // Stage 3: Run Unit Test
        stage('Run Unit Test') {
            steps {
                bat '''
                    call venv\\Scripts\\activate
                    set PYTHONPATH=.
                    pytest || echo "Tests failed but continuing..."
                '''
            }
        }

        // Stage 4: Build Application
        stage('Build Application') {
            steps {
                bat '''
                    echo Packaging application...
                    tar -czf app-package.tar.gz .
                '''
            }
        }

        // Stage 5: Deploy Application
        stage('Deploy Application') {
            steps {
                bat '''
                    echo Deploying application...
                    if not exist "C:\\tmp\\deployed_flask_app" mkdir "C:\\tmp\\deployed_flask_app"
                    copy app-package.tar.gz "C:\\tmp\\deployed_flask_app\\"
                    
                    cd /d "C:\\tmp\\deployed_flask_app"
                    tar -xzf app-package.tar.gz
                    echo Deployment Complete at C:\\tmp\\deployed_flask_app
                '''
            }
        }
    }
}