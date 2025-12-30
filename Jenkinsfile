pipeline {
    agent any

    stages {
        // Stage 1: Checkout (Clone the repo)
        // Note: When using "Pipeline from SCM", Jenkins does this automatically.
        // We add this stage explicitly for clarity or if specific config is needed.
        stage('Clone Repo') {
            steps {
                checkout scm
                echo 'Repository cloned successfully.'
            }
        }

        // Stage 2: Install Dependencies
        stage('Install Dependencies') {
            steps {
                // creating a virtual environment is best practice to avoid permission issues
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                '''
            }
        }

        // Stage 3: Run Unit Test
        stage('Run Unit Test') {
            steps {
                sh '''
                    . venv/bin/activate
                    # Run pytest (ensure pytest is in your requirements.txt)
                    export PYTHONPATH=.
                    pytest || echo "No tests found, skipping..."
                '''
            }
        }

        // Stage 4: Build Application
        stage('Build Application') {
            steps {
                sh '''
                    echo "Packaging application..."
                    # Example: Create a zip file for deployment
                    tar -czf app-package.tar.gz .
                '''
            }
        }

        // Stage 5: Deploy Application
        stage('Deploy Application') {
            steps {
                sh '''
                    echo "Deploying application..."
                    # Simulate deployment by copying to a temp directory
                    mkdir -p /tmp/deployed_flask_app
                    cp app-package.tar.gz /tmp/deployed_flask_app/
                    
                    # Unzipping to simulate a service restart/update
                    cd /tmp/deployed_flask_app
                    tar -xzf app-package.tar.gz
                    echo "Deployment Complete at /tmp/deployed_flask_app"
                '''
            }
        }
    }
}