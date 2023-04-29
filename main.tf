terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "4.65.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

module "lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "4.16.0"
}

module "s3_bucket" {
  source = "terraform-aws-modules/s3-bucket/aws"

  bucket = var.s3_bucket_name
  acl    = "private"

  control_object_ownership = true
  object_ownership         = "ObjectWriter"

  versioning = {
    enabled = true
  }
  tags = {
    Name = "inventory-checker"
  }
}

module "lambda_function" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "inventory-checker"
  description   = "Inventory checker lambda function"
  handler       = "app.lambda_handler"
  runtime       = "python3.10"
  timeout       = 300

  source_path = "./app/app.py"

  environment_variables = {
    "WEBHOOK_URL"   = var.webhook_url
    "S3_BUCKET_ARN" = module.s3_bucket.s3_bucket_arn
  }

  tags = {
    Name = "inventory-checker"
  }
}

module "eventbridge" {
  source = "terraform-aws-modules/eventbridge/aws"

  create_bus = false

  rules = {
    crons = {
      description         = "Trigger for Inventory checker lambda"
      schedule_expression = "cron(0 9,21 * * ? *)"
    }
  }

  targets = {
    crons = [
      {
        name  = "lambda-loves-cron"
        arn   = module.lambda_function.lambda_function_arn
        input = jsonencode({ "job" : "cron-by-rate" })
      }
    ]
  }

  tags = {
    Name = "inventory-checker"
  }
}

module "iam_policy" {
  source = "terraform-aws-modules/iam/aws//modules/iam-policy"

  name        = "inventory-checker-exec-role"
  path        = "/"
  description = "IAM policy to access inventory checker S3 bucket"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
        "Effect": "Allow",
        "Action": [
            "logs:PutLogEvents",
            "logs:CreateLogGroup",
            "logs:CreateLogStream"
        ],
        "Resource": "arn:aws:logs:*:*:*"
    },
    {
        "Effect": "Allow",
        "Action": [
            "s3:GetObject"
        ],
        "Resource": "${module.s3_bucket.s3_bucket_arn}/*"
    },
  ]
}
EOF
  tags = {
    Name = "inventory-checker"
  }
}