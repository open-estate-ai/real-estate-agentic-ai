#!/bin/bash
# this is a wrapper command for the terraform with predefined commands.

# example command
# ./tf-wrapper.sh dev init
# ./tf-wrapper.sh dev plan
# ./tf-wrapper.sh dev apply

# Pre-requisites
# ??

# optional
# export TF_LOG=warn

export env=$1
action=$2
src_dir=./tf-real-estate-agents

if [[ -z ${env} ]]; then
    echo env not defined
    exit 2
fi

if [[ -z ${src_dir} ]]; then
    echo service not defined
    exit 2
fi

# Remove temp dir
rm -r "${src_dir}/../temp" 2>/dev/null

case $action in
    init)
    rm -rf "${src_dir}"/.terraform*
    # terraform -chdir="${src_dir}" "${action}" -upgrade=true -reconfigure -compact-warnings -backend-config="../tf-vars/${env}/backend.tf"
    terraform -chdir="${src_dir}" "${action}" -upgrade=true -reconfigure -compact-warnings -backend-config="path=../tf-vars/${env}/terraform.tfstate"
    ;;
    apply)
    terraform -chdir="${src_dir}" "${action}" -auto-approve --var-file="../tf-vars/${env}/params-env.tfvars" ${3} ${4}
    ;;
    plan|destroy)
    terraform -chdir="${src_dir}" "${action}" --var-file="../tf-vars/${env}/params-env.tfvars" ${3}
    ;;
    force-unlock)
    terraform -chdir="${src_dir}" "${action}" ${3}
    ;;
    output)
    terraform -chdir="${src_dir}" "${action}" -raw ${3}
    ;;
    import)
    terraform -chdir="${src_dir}" "${action}" --var-file="../tf-vars/${env}/param-component.tfvars" --var-file="../tf-vars/${env}/params-env.tfvars" -generate-config-out="./tf-import-configs/generated.tf"
    ;;
    *)

    echo "action should be any one of the below" >&2
    echo "init, plan, apply, destroy, force-unlock, output, import" >&2
    exit 1
    ;;
esac
