#!/usr/bin/env groovy

pipeline {
    agent { label 'python2' }
    stages {
        stage('Run unit tests') {
            steps {
                sh 'tox'
            }
        }
        stage('Build source distribution') {
            steps {
                sh 'python2.7 setup.py sdist'
                archiveArtifacts artifacts: 'dist/pybofh-*.tar.gz'
            }
        }
        stage('Build documentation') {
            steps {
                sh '''
                python2.7 setup.py build_sphinx
                tar -czv -C build/sphinx/html -f pybofh-docs.tar.gz .
                '''
                archiveArtifacts artifacts: 'pybofh-docs.tar.gz'
            }
        }
    }
    post {
        always {
            junit '**/junit*.xml'
        }
        cleanup {
            sh 'rm -vf junit*.xml'
            sh 'rm -vrf build dist'
            sh 'rm -vf pybofh-docs.tar.gz'
        }
    }
}
