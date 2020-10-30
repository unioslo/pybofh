#!/usr/bin/env groovy

def version = '0.0.0'
def docdir = 'bofh-docs'

pipeline {
    agent { label 'python' }
    stages {
        stage('Gather facts') {
            steps {
                script {
                    version = sh (
                        script: 'python setup.py --version',
                        returnStdout: true,
                    ).trim()
                    echo "version: ${version}"
                }
            }
        }
        stage('Run unit tests') {
            steps {
                sh 'tox'
            }
        }
        stage('Build source distribution') {
            steps {
                sh 'python setup.py sdist'
                archiveArtifacts artifacts: 'dist/bofh-*.tar.gz'
            }
        }
        stage('Build documentation') {
            steps {
                script {
                    docdir = "bofh-docs-${version}"
                }
                sh """
                python setup.py build_sphinx
                mv build/sphinx/html "build/sphinx/${docdir}"
                tar -czv -C build/sphinx -f "${docdir}.tar.gz" "${docdir}"
                """
                archiveArtifacts artifacts: "${docdir}.tar.gz"
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
            sh 'rm -vf bofh-docs*.tar.gz'
        }
    }
}
