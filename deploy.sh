
# Package SAM template
sam package --template-file template.yaml --s3-bucket "$1"  --output-template-file packaged.yaml

echo "Package Done... Deploying the service now."
# Deploy packaged SAM template
sam deploy --template-file ./packaged.yaml --stack-name ENIReporter --capabilities CAPABILITY_IAM
aws cloudformation describe-stacks --stack-name ENIReporter \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiURL`].OutputValue' \
    --output text
