#!groovy

/// file: compile-all-werks.groovy

def main() {
    def docker_args = "${mount_reference_repo_dir}";

    def target_path = "/home/mkde/werks/all_werks_v2.json";
    def targets_credentials = [
        [env.WEB_STAGING, "web-staging"],
        ["checkmk.com", "checkmk-deploy"],
        ["customer.checkmk.com", "customer-deploy"]
    ];

    print(
        """
        |===== CONFIGURATION ===============================
        |docker_args:.............. │${docker_args}│
        |checkout_dir:............. │${checkout_dir}│
        |===================================================
        """.stripMargin());

    stage("Checkout repositories") {
        // this will checkout the repo at "${WORKSPACE}/${repo_name}"
        // but check again if you modify it here
        provide_clone("checkmk_kube_agent", "ssh-git-gerrit-jenkins");
        provide_clone("cma", "ssh-git-gerrit-jenkins");
    }

    stage("Compile werks") {
        docker.withRegistry(DOCKER_REGISTRY, 'nexus') {
            docker_image_from_alias("IMAGE_TESTING").inside("${docker_args}") {
                dir("${checkout_dir}") {
                    sh("""
                        scripts/run-pipenv run echo build venv...
                        scripts/run-pipenv run python3 -m cmk.utils.werks collect cmk ./ > cmk.json
                        scripts/run-pipenv run python3 -m cmk.utils.werks collect cma ${WORKSPACE}/cma > cma.json
                        scripts/run-pipenv run python3 -m cmk.utils.werks collect checkmk_kube_agent ${WORKSPACE}/checkmk_kube_agent > kube.json

                        # jq -s '.[0] * .[1] * .[2]' cma.json cmk.json kube.json > all_werks.json
                        # no need to install jq!!!!!
                        python3 -c 'import json, sys; print(json.dumps({k: v for f in sys.argv[1:] for k, v in json.load(open(f)).items()}, indent=4))' \
                            cmk.json \
                            cma.json \
                            kube.json \
                            > all_werks.json
                    """);

                    archiveArtifacts(
                        artifacts: "all_werks.json",
                        fingerprint: true,
                    );
                }
            }
        }
    }

    stage("Validate HTML") {
        docker.withRegistry(DOCKER_REGISTRY, 'nexus') {
            docker_image_from_alias("IMAGE_TESTING").inside("${docker_args}") {
                dir("${checkout_dir}") {
                    try {
                        sh(script: """
                            ./scripts/npm-ci
                            echo '<!DOCTYPE html><html lang="en"><head><title>werks</title></head><body>' > validate-werks.html
                            # still no need for jq!
                            python3 -c 'import json; print("\\n".join(("\\n\\n<p>{}</p>\\n{}".format(key, value["description"]) for key, value in json.load(open("all_werks.json")).items())))' >> validate-werks.html
                            echo '</body></html>' >> validate-werks.html
                            java \
                                -jar node_modules/vnu-jar/build/dist/vnu.jar \
                                --filterpattern 'The .tt. element is obsolete\\. Use CSS instead\\.' \
                                --stdout \
                                --format gnu \
                                - < validate-werks.html \
                                > validate-werks.error.txt
                        """);
                    } catch(Exception e) {
                        archiveArtifacts(
                            artifacts: "validate-werks.*, all_werks.json",
                            fingerprint: true,
                        );
                        sh("""
                            cat "validate-werks.error.txt"
                            echo "Found invalid HTML. See errors above, compare the line numbers with validate-werks.html artifact."
                        """);
                        throw e;
                    }
                }
            }
        }
    }

    targets_credentials.each{target_credential ->
        def target = target_credential[0];
        def credentials_id = target_credential[1];

        stage("Update werks on ${target}") {
            withCredentials([
                sshUserPrivateKey(credentialsId: credentials_id, keyFileVariable: 'keyfile', usernameVariable: 'user')
            ]) {
                sh("""
                    rsync --verbose \
                        -e "ssh -o StrictHostKeyChecking=no -i ${keyfile} -p ${WEB_STAGING_PORT}" \
                        ${WORKSPACE}/all_werks.json \
                        ${user}@${target}:${target_path}
                """);
            }
        }
    }
}

return this;
