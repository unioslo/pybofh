#!/usr/bin/env groovy

def version = '0.0.0'
def docdir = 'pybofh-docs'

pipeline {
    agent { label 'python2' }
    stages {
        stage('Gather facts') {
            steps {
                script {
                    version = sh (
                        script: 'python2.7 setup.py --version',
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
                sh 'python2.7 setup.py sdist'
                archiveArtifacts artifacts: 'dist/pybofh-*.tar.gz'
            }
        }
        stage('Build documentation') {
            steps {
                script {
                    docdir = "pybofh-docs-${version}"
                }
                sh """
                python2.7 setup.py build_sphinx
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
            sh 'rm -vf pybofh-docs*.tar.gz'
        }
    }
}
